from app.repositories.class_repository import ClassRepository, SectionRepository


class ClassService:
    def __init__(self, class_repo: ClassRepository, section_repo: SectionRepository):
        self.class_repo = class_repo
        self.section_repo = section_repo

    async def create_class(self, school_id: str, year_id: str, data: dict):
        return await self.class_repo.create(school_id, data)

    async def duplicate_classes_for_new_year(self, school_id: str, from_year_id: str, to_year_id: str) -> int:
        source_classes = await self.class_repo.list_by_school_year(school_id, from_year_id)
        if not source_classes:
            return 0

        created_count = 0
        for source in source_classes:
            existing_targets = await self.class_repo.list_by_school_year(school_id, to_year_id)
            if any(x.name == source.name for x in existing_targets):
                continue

            new_class = await self.class_repo.create(
                school_id,
                {
                    "academic_year_id": to_year_id,
                    "name": source.name,
                    "is_active": True,
                },
            )
            await self.section_repo.duplicate_sections(str(source.id), str(new_class.id))
            created_count += 1

        return created_count

