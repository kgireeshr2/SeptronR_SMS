import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.staff import Staff
from app.models.foundation import SchoolSetting


async def generate_employee_id(
    db: AsyncSession, school_id: str, custom_format: Optional[str] = None
) -> str:
    """
    Generate a unique employee ID for a staff member.
    
    Format can be customized via school settings:
    - Default: EMP-{seq} (e.g., EMP-0001, EMP-0002)
    - Custom: STF-{seq}, EMP{year}-{seq}, etc.
    
    Args:
        db: Database session
        school_id: School UUID
        custom_format: Optional custom format string (overrides school settings)
    
    Returns:
        str: Generated employee ID
    """
    # Get format from school settings if not provided
    if not custom_format:
        result = await db.execute(
            select(SchoolSetting.value)
            .where(
                SchoolSetting.school_id == school_id,
                SchoolSetting.key == "employee_id_format",
            )
        )
        format_setting = result.scalar_one_or_none()
        custom_format = format_setting if format_setting else "EMP-{seq}"

    # Get the highest employee_id sequence number for this school
    result = await db.execute(
        select(Staff.employee_id)
        .where(Staff.school_id == school_id, Staff.deleted_at.is_(None))
        .order_by(Staff.employee_id.desc())
    )
    existing_ids = result.scalars().all()

    # Extract sequence numbers from existing IDs matching the format pattern
    seq_pattern = re.sub(r"\{seq\}", r"([0-9]+)", custom_format)
    seq_pattern = re.sub(r"\{year\}", r"[0-9]{4}", seq_pattern)
    
    max_seq = 0
    for emp_id in existing_ids:
        match = re.match(seq_pattern, emp_id)
        if match:
            try:
                seq = int(match.group(1))
                if seq > max_seq:
                    max_seq = seq
            except (ValueError, IndexError):
                continue

    # Generate new sequence
    new_seq = max_seq + 1

    # Replace placeholders in format
    from datetime import datetime
    current_year = datetime.now().year
    
    employee_id = custom_format.replace("{seq}", str(new_seq).zfill(4))
    employee_id = employee_id.replace("{year}", str(current_year))

    # Check for collision (unlikely but possible with custom formats)
    collision_check = await db.execute(
        select(Staff.id).where(
            Staff.school_id == school_id,
            Staff.employee_id == employee_id,
            Staff.deleted_at.is_(None),
        )
    )
    if collision_check.scalar_one_or_none():
        # Recursively try next sequence
        return await generate_employee_id(
            db, school_id, custom_format.replace(str(new_seq).zfill(4), str(new_seq + 1).zfill(4))
        )

    return employee_id
