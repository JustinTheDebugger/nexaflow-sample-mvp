"""
Media storage helpers for NexaFlow sample workflows.

The Streamlit MVP stores uploaded files locally.
Database metadata is handled separately by the repository layer.

This storage implementation can later be replaced by
Supabase or another object-storage service.
"""

from pathlib import Path
from uuid import uuid4


MEDIA_ROOT = Path("storage/sample_media")


def save_sample_media_file(
    uploaded_file,
    record_id,
):
    """
    Save an uploaded media file locally.

    Each record receives its own folder.

    Returns the stored file path as a string.
    """

    record_folder = (
        MEDIA_ROOT
        / str(record_id)
    )

    record_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    extension = Path(
        uploaded_file.name
    ).suffix.lower()

    filename = (
        f"{uuid4().hex}{extension}"
    )

    file_path = (
        record_folder
        / filename
    )

    with file_path.open("wb") as file_handle:
        file_handle.write(
            uploaded_file.getbuffer()
        )

    return str(file_path)



def delete_sample_media_file(
    storage_path,
):
    """
    Delete a locally stored media file.

    Also removes the parent folder if it becomes empty.
    """

    if not storage_path:
        return

    file_path = Path(storage_path)

    if file_path.exists():
        file_path.unlink()

    parent_folder = file_path.parent

    if (
        parent_folder.exists()
        and parent_folder != MEDIA_ROOT
        and not any(parent_folder.iterdir())
    ):
        parent_folder.rmdir()