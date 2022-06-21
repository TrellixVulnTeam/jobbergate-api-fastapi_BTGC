"""
Provides logic for migrating job_submission data from legacy db to nextgen db.
"""
from loguru import logger


def migrate_job_submissions(nextgen_db, legacy_job_submissions, user_map, job_scripts_map):
    """
    Inserts job_submission data to nextgen database.

    Given a list of legacy job_submissions, a user map, and a job_script map, create
    records in the nextgen database for each job_submission.
    """
    logger.info("Migrating job_submissions to nextgen database")
    for job_submission in legacy_job_submissions:
        owner_email = user_map[job_submission["job_submission_owner_id"]]["email"]
        nextgen_job_script_id = job_scripts_map[job_submission["job_script_id"]]
        try:
            slurm_job_id = int(job_submission["slurm_job_id"])
        except ValueError:
            slurm_job_id = None

        nextgen_db.execute(
            """
            insert into job_submissions (
                job_submission_name,
                job_submission_description,
                job_submission_owner_email,
                job_script_id,
                slurm_job_id,
                created_at,
                updated_at
            )
            values (
                %(name)s,
                %(description)s,
                %(owner_email)s,
                %(job_script_id)s,
                %(slurm_job_id)s,
                %(created)s,
                %(updated)s
            )
            returning id
            """,
            dict(
                name=job_submission["job_submission_name"],
                description=job_submission["job_submission_description"],
                owner_email=owner_email,
                job_script_id=nextgen_job_script_id,
                slurm_job_id=slurm_job_id,
                created=job_submission["created_at"],
                updated=job_submission["updated_at"],
            ),
        )
    logger.success("Finished migrating job_submissions")
