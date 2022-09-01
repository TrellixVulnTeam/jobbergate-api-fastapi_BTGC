"""
Provide a convenience class for managing application files.
"""

from functools import partial
from pathlib import Path, PurePath
from typing import Callable, Dict, List, Optional

from fastapi import UploadFile
from file_storehouse import FileManager
from loguru import logger
from pydantic import BaseModel, Field

from jobbergate_api.config import settings
from jobbergate_api.file_validation import perform_all_checks_on_uploaded_files
from jobbergate_api.s3_manager import IO_TRANSFORMATIONS, file_manager_factory, s3_client

APPLICATIONS_WORK_DIR = "applications"
APPLICATION_CONFIG_FILE_NAME = "jobbergate.yaml"
APPLICATION_SOURCE_FILE_NAME = "jobbergate.py"
APPLICATION_TEMPLATE_FOLDER = "templates"

s3man_applications_factory: Callable[[int], FileManager] = partial(
    file_manager_factory,
    s3_client=s3_client,
    bucket_name=settings.S3_BUCKET_NAME,
    work_directory=Path(APPLICATIONS_WORK_DIR),
    manager_cls=FileManager,
    transformations=IO_TRANSFORMATIONS,
)


class ApplicationFiles(BaseModel):
    """
    Model containing application files.
    """

    config_file: Optional[str] = Field(None, alias="application_config")
    source_file: Optional[str] = Field(None, alias="application_source_file")
    templates: Optional[Dict[str, str]] = Field(default_factory=dict, alias="application_templates")

    class Config:
        allow_population_by_field_name = True

    @classmethod
    def get_from_s3(cls, application_id: int):
        """
        Alternative method to initialize the model getting the objects from S3.
        """
        logger.debug(f"Getting application files from S3: {application_id=}")
        file_manager = s3man_applications_factory(application_id)

        application_files = cls(
            config_file=file_manager.get(APPLICATION_CONFIG_FILE_NAME),
            source_file=file_manager.get(APPLICATION_SOURCE_FILE_NAME),
        )

        for path in file_manager.keys():
            if str(path.parent) == APPLICATION_TEMPLATE_FOLDER:
                filename = path.name
                application_files.templates[filename] = file_manager.get(path)

        logger.debug("Success getting application files from S3")

        if not application_files.config_file:
            logger.warning("Application config file was not found")
        if not application_files.source_file:
            logger.warning("Application source file was not found")
        if not application_files.templates:
            logger.warning("No template file was found")

        return application_files

    @classmethod
    def delete_from_s3(cls, application_id: int):
        """
        Deleted the files associated with the given id.
        """
        logger.debug(f"Deleting from S3 the files associated to {application_id=}")
        file_manager = s3man_applications_factory(application_id)
        file_manager.clear()
        logger.debug(f"Files were deleted for {application_id=}")

    def write_to_s3(self, application_id: int, *, remove_previous_files: bool = True):
        """
        Write to s3 the files associated with a given id.
        """
        logger.debug(f"Writing the application files to S3: {application_id=}")

        if remove_previous_files:
            self.delete_from_s3(application_id)

        file_manager = s3man_applications_factory(application_id)

        if self.config_file:
            path = Path(APPLICATION_CONFIG_FILE_NAME)
            file_manager[path] = self.config_file

        if self.source_file:
            path = Path(APPLICATION_SOURCE_FILE_NAME)
            file_manager[path] = self.source_file

        for name, content in self.templates.items():
            path = Path(APPLICATION_TEMPLATE_FOLDER, name)
            file_manager[path] = content

        logger.debug(f"Files were written for {application_id=}")

    @classmethod
    def get_from_upload_files(cls, upload_files: List[UploadFile]):
        """
        Initialize the model getting the objects from a list of uploaded files.
        """
        logger.debug("Getting application files from the uploaded files")

        perform_all_checks_on_uploaded_files(upload_files)

        application_files = cls()

        for upload in upload_files:
            if upload.filename.endswith(".py"):
                application_files.source_file = upload.file.read().decode("utf-8")
                upload.file.seek(0)
            elif upload.filename.endswith(".yaml"):
                application_files.config_file = upload.file.read().decode("utf-8")
                upload.file.seek(0)
            elif upload.filename.endswith((".j2", ".jinja2")):
                filename = PurePath(upload.filename).name
                application_files.templates[filename] = upload.file.read().decode("utf-8")
                upload.file.seek(0)

        logger.debug("Success getting application files from the uploaded files")

        return application_files
