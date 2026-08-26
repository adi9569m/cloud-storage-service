"""Tests for SQLAlchemy ORM models schema definition and relationship consistency."""

import uuid
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, configure_mappers
from app.core.database import Base
from app.models import (
    User,
    Folder,
    File,
    FileVersion,
    Share,
    ShareRole,
    LinkShare,
    Star,
    Activity,
)


def test_models_mapper_configuration():
    """Verify that all model relationships and mappers are configured correctly."""
    # configure_mappers() will raise InvalidRequestError if any relationship or foreign key is misconfigured
    configure_mappers()

    # Check table names registered in Base metadata
    expected_tables = {
        "users",
        "folders",
        "files",
        "file_versions",
        "shares",
        "link_shares",
        "stars",
        "activities",
    }
    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(registered_tables), f"Missing tables: {expected_tables - registered_tables}"


def test_models_in_memory_creation():
    """Verify tables can be created and basic relationships work in SQLite."""
    sqlite_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=sqlite_engine)

    Session = sessionmaker(bind=sqlite_engine)
    session = Session()

    # Create a user
    user = User(
        email="test@example.com",
        hashed_password="hashed_pw_example",
        full_name="Test User",
    )
    session.add(user)
    session.commit()
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True

    # Create a folder owned by user
    folder = Folder(
        name="Documents",
        owner_id=user.id,
    )
    session.add(folder)
    session.commit()
    assert folder.id is not None
    assert folder.owner.id == user.id

    # Create a subfolder
    subfolder = Folder(
        name="Reports",
        owner_id=user.id,
        parent_id=folder.id,
    )
    session.add(subfolder)
    session.commit()
    assert subfolder.parent.id == folder.id

    # Create a file
    file = File(
        name="sales_2026.pdf",
        folder_id=folder.id,
        owner_id=user.id,
        mime_type="application/pdf",
        size_bytes=1024,
        storage_path=f"uploads/{user.id}/files/{uuid.uuid4()}_sales_2026.pdf",
    )
    session.add(file)
    session.commit()
    assert file.id is not None
    assert file.folder.id == folder.id

    # Create a file version
    version = FileVersion(
        file_id=file.id,
        version_number=1,
        storage_path=file.storage_path,
        size_bytes=1024,
        mime_type="application/pdf",
        uploaded_by_id=user.id,
    )
    session.add(version)
    session.commit()
    assert len(file.versions) == 1
    assert file.versions[0].id == version.id

    # Create another user for sharing
    recipient = User(
        email="recipient@example.com",
        hashed_password="recipient_pw",
        full_name="Recipient User",
    )
    session.add(recipient)
    session.commit()

    # Create a direct share
    share = Share(
        granter_id=user.id,
        grantee_id=recipient.id,
        file_id=file.id,
        role=ShareRole.EDITOR,
    )
    session.add(share)
    session.commit()
    assert share.role == ShareRole.EDITOR
    assert share.granter.id == user.id
    assert share.grantee.id == recipient.id

    # Create a link share
    link = LinkShare(
        token="secure-test-token-123456",
        created_by_id=user.id,
        file_id=file.id,
        role=ShareRole.VIEWER,
    )
    session.add(link)
    session.commit()
    assert link.token == "secure-test-token-123456"

    # Create a star
    star = Star(
        user_id=user.id,
        file_id=file.id,
    )
    session.add(star)
    session.commit()
    assert star.file.id == file.id

    # Create an activity
    activity = Activity(
        user_id=user.id,
        action="FILE_UPLOAD",
        resource_type="FILE",
        resource_id=file.id,
        details={"filename": file.name, "size": file.size_bytes},
    )
    session.add(activity)
    session.commit()
    assert activity.action == "FILE_UPLOAD"
    assert activity.user.id == user.id

    session.close()
