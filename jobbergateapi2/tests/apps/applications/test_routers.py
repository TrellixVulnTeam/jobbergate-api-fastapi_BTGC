"""
Tests for the /applications/ endpoint.
"""
from io import StringIO
from unittest import mock

import nest_asyncio
import pytest
from fastapi import status

from jobbergateapi2.apps.applications.models import applications_table
from jobbergateapi2.apps.applications.schemas import Application
from jobbergateapi2.apps.users.models import users_table
from jobbergateapi2.apps.users.schemas import UserCreate
from jobbergateapi2.storage import database
from jobbergateapi2.tests.apps.conftest import insert_objects

# because the http test client runs an event loop fot itself,
# this lib is necessary to avoid the errror "this event loop
# is already running"
nest_asyncio.apply()


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_create_application(boto3_client_mock, application_data, client, user_data):
    """
    Test POST /applications/ correctly creates an application.

    This test proves that an application is successfully created via a POST request to the /applications/
    endpoint. We show this by asserting that the application is created in the database after the post
    request is made, the correct status code (201) is returned and the correct boto3 method was called.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    file_mock = mock.MagicMock(wraps=StringIO("test"))

    user = [UserCreate(**user_data)]
    await insert_objects(user, users_table)

    response = client.post("/applications/", data=application_data, files={"upload_file": file_mock})
    assert response.status_code == status.HTTP_201_CREATED
    s3_client_mock.put_object.assert_called_once()

    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_create_without_application_name(boto3_client_mock, application_data, client, user_data):
    """
    Test that is not possible to create an application without the required parameters.

    This test proves that is not possible to create an application without the name. We show this by
    trying to create an application without the application_name in the request then assert that the
    application still does not exists in the database, the correct status code (422) is returned and that the
    boto3 method is never called.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    file_mock = mock.MagicMock(wraps=StringIO("test"))

    user = [UserCreate(**user_data)]
    await insert_objects(user, users_table)

    application_data["application_name"] = None
    response = client.post("/applications/", data=application_data, files={"upload_file": file_mock})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    s3_client_mock.put_object.assert_not_called()

    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 0


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_create_without_file(boto3_client_mock, application_data, client, user_data):
    """
    Test that is not possible to create an application without a file.

    This test proves that is not possible to create an application without a file. We show this by
    trying to create an application without a file in the request then assert that the application still
    does not exists in the database, the correct status code (422) is returned and that the boto3 method
    is never called.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock

    user = [UserCreate(**user_data)]
    await insert_objects(user, users_table)

    application_data["application_name"] = None
    response = client.post("/applications/", data=application_data)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    s3_client_mock.put_object.assert_not_called()

    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 0


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_delete_application(boto3_client_mock, client, user_data, application_data):
    """
    Test DELETE /applications/<id> correctly deletes an application.

    This test proves that an application is successfully deleted via a DELETE request to the
    /applciations/<id> endpoint. We show this by asserting that the application no longer exists in the
    database after the delete request is made, the correct status code is returned and the correct boto3
    method was called.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    application = [Application(application_owner_id=1, **application_data)]
    await insert_objects(application, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    response = client.delete("/applications/1")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 0
    s3_client_mock.delete_object.assert_called_once()


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_delete_application_not_from_user(boto3_client_mock, client, user_data, application_data):
    """
    Test that a userX cannot delete an application owned by userY.

    This test proves that userX cannot delete an application owned by userY. We show this by
    asserting that the application owned by userY still exists after userX tries to delete it, that
    the correct response code (404) is returned and that the boto3 method is never called.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    application = [Application(id=1, application_owner_id=999, **application_data)]
    await insert_objects(application, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    response = client.delete("/applications/1")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1
    s3_client_mock.delete_object.assert_not_called()


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_delete_application_not_found(boto3_client_mock, client, user_data, application_data):
    """
    Test DELETE /applications/<id> the correct response code when the application doesn't exist.

    This test proves that DELETE /applications/<id> returns the correct response code (404)
    when the application id does not exist in the database. We show this by asserting that a 404 response
    code is returned for a request made with an application id that doesn't exist.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    application = [Application(id=1, application_owner_id=1, **application_data)]
    await insert_objects(application, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    response = client.delete("/applications/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1
    s3_client_mock.delete_object.assert_not_called()


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_delete_application_without_id(boto3_client_mock, client, user_data, application_data):
    """
    Test DELETE /applications/ without <id> returns the correct response.

    This test proves that DELETE /applications returns the correct response code (405)
    when an application id is not specified. We show this by asserting that a 405 response
    code is returned for a request made without an application id.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    response = client.delete("/applications/")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    s3_client_mock.delete_object.assert_not_called()


@pytest.mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_application_by_id(client, user_data, application_data):
    """
    Test GET /applications/<id>.

    This test proves that GET /applications/<id> returns the correct application, owned by
    the user making the request. We show this by asserting that the application data
    returned in the response is equal to the application data that exists in the database
    for the given application id.
    """
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    application = [Application(id=1, application_owner_id=1, **application_data)]
    await insert_objects(application, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    response = client.get("/applications/1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["id"] == 1
    assert data["application_name"] == application_data["application_name"]
    assert data["application_config"] == application_data["application_config"]
    assert data["application_file"] == application_data["application_file"]


@pytest.mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_application_by_id_invalid(client, user_data, application_data):
    """
    Test the correct response code is returned when an application does not exist.

    This test proves that GET /application/<id> returns the correct response code when the
    requested application does not exist. We show this by asserting that the status code
    returned is what we would expect given the application requested doesn't exist (404).
    """
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    response = client.get("/applications/10")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_application_all_from_user(client, user_data, application_data):
    """
    Test GET /applications returns only applications owned by the user making the request.

    This test proves that GET /applications returns the correct applications for the user making
    the request. We show this by asserting that the applications returned in the response are
    only applications owned by the user making the request.
    """
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    applications = [
        Application(id=1, application_owner_id=1, **application_data),
        Application(id=2, application_owner_id=1, **application_data),
        Application(id=3, application_owner_id=999, **application_data),
    ]
    await insert_objects(applications, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 3

    response = client.get("/applications/")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2


@pytest.mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_application_all_from_user_empty(client, user_data, application_data):
    """
    Test applications list doesn't include applications owned by other users.

    This test proves that the user making the request cannot see applications owned by other users.
    We show this by creating applications that are owned by another user id and assert that
    the user making the request to list applications doesn't see any of the other user's
    applications in the response, len(resp.json()) == 0.
    """
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    applications = [
        Application(id=1, application_owner_id=999, **application_data),
        Application(id=2, application_owner_id=999, **application_data),
        Application(id=3, application_owner_id=999, **application_data),
    ]
    await insert_objects(applications, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 3

    response = client.get("/applications/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 0


@pytest.mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_all_applications(client, user_data, application_data):
    """
    Test that listing applications, when all=True, contains applications owned by other users.

    This test proves that the user making the request can see applications owned by other users.
    We show this by creating three applications, two that are owned by the user making the request, and one
    anther owned by another user. Assert that the response to GET /applications?all=True includes all three
    applications.
    """
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    applications = [
        Application(id=1, application_owner_id=1, **application_data),
        Application(id=2, application_owner_id=1, **application_data),
        Application(id=3, application_owner_id=999, **application_data),
    ]
    await insert_objects(applications, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 3

    response = client.get("/applications/?all=True")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data) == 3
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[2]["id"] == 3


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_update_application(boto3_client_mock, client, user_data, application_data):
    """
    Test that an application is updated via PUT.

    This test proves that an application's values are correctly updated following a PUT request to the
    /application/<id> endpoint. We show this by asserting that the values provided to update the
    application are returned in the response made to the PUT /applciation/<id> endpoint.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    file_mock = mock.MagicMock(wraps=StringIO("test"))
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    applications = [
        Application(
            id=1, application_owner_id=1, application_description="old description", **application_data
        ),
    ]
    await insert_objects(applications, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    application_data["application_name"] = "new_name"
    application_data["application_description"] = "new_description"
    response = client.put("/applications/1", data=application_data, files={"upload_file": file_mock})
    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["application_name"] == application_data["application_name"]
    assert data["application_description"] == application_data["application_description"]

    s3_client_mock.put_object.assert_called_once()


@pytest.mark.asyncio
@mock.patch("jobbergateapi2.apps.applications.routers.boto3")
@database.transaction(force_rollback=True)
async def test_update_application_wrong_user(boto3_client_mock, client, user_data, application_data):
    """
    Test that an userX cannot update an application owned by userY.

    This test proves that userX cannot update an application owned by userY. We show this by
    asserting that the application id doesn't exist for the user making the request and the
    expected response is returned.
    """
    s3_client_mock = mock.Mock()
    boto3_client_mock.client.return_value = s3_client_mock
    file_mock = mock.MagicMock(wraps=StringIO("test"))
    user = [UserCreate(id=1, **user_data)]
    await insert_objects(user, users_table)

    applications = [
        Application(id=1, application_owner_id=2, **application_data),
    ]
    await insert_objects(applications, applications_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM applications")
    assert count[0][0] == 1

    response = client.put("/applications/1", data=application_data, files={"upload_file": file_mock})
    assert response.status_code == status.HTTP_404_NOT_FOUND

    s3_client_mock.put_object.assert_not_called()
