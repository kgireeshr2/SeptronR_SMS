"""
Utility for generating unique admission numbers based on school settings.
"""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.students import Student
from app.models.foundation import SchoolSetting
import re


async def generate_admission_number(
    session: AsyncSession,
    school_id: UUID,
) -> str:
    """
    Generate a unique admission number for a student based on school settings.
    
    Format: PREFIX-YEAR-SEQUENCE
    Example: STD-2024-001
    
    Args:
        session: Database session
        school_id: School UUID
        
    Returns:
        Generated admission number string
    """
    # Get school settings for admission number format
    result = await session.execute(
        select(SchoolSetting)
        .where(SchoolSetting.school_id == school_id)
        .where(SchoolSetting.key == "admission_number_format")
    )
    setting = result.scalar_one_or_none()
    
    # Default format if not configured
    format_template = setting.value if setting else "STD-{YEAR}-{SEQ:04d}"
    
    # Extract year placeholder
    from datetime import datetime
    current_year = datetime.utcnow().year
    
    # Parse the format to determine prefix and sequence length
    # Example formats: "STD-{YEAR}-{SEQ:04d}", "ADM{YEAR}{SEQ:03d}"
    year_placeholder = "{YEAR}"
    seq_pattern = r"\{SEQ:0(\d+)d\}"
    
    # Find sequence length from format
    seq_match = re.search(seq_pattern, format_template)
    seq_length = int(seq_match.group(1)) if seq_match else 4
    
    # Get the highest admission number for this school
    result = await session.execute(
        select(func.max(Student.admission_number))
        .where(Student.school_id == school_id)
        .where(Student.deleted_at.is_(None))
    )
    max_admission_number = result.scalar_one_or_none()
    
    # Determine next sequence number
    if max_admission_number:
        # Extract sequence from existing admission number
        # Try to find digits at the end
        digits_match = re.search(r"(\d+)$", max_admission_number)
        if digits_match:
            last_sequence = int(digits_match.group(1))
            next_sequence = last_sequence + 1
        else:
            next_sequence = 1
    else:
        next_sequence = 1
    
    # Verify uniqueness and find the first non-colliding sequence number
    while True:
        # Generate admission number using format
        admission_number = format_template.replace(year_placeholder, str(current_year))
        admission_number = re.sub(seq_pattern, f"{{SEQ:0{seq_length}d}}", admission_number)
        admission_number = admission_number.format(SEQ=next_sequence)

        result = await session.execute(
            select(Student)
            .where(Student.school_id == school_id)
            .where(Student.admission_number == admission_number)
            .where(Student.deleted_at.is_(None))
        )
        existing = result.scalar_one_or_none()

        if not existing:
            break
        # Collision — try next sequence number
        next_sequence += 1

    return admission_number
