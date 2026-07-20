"""
Seed default templates for all existing schools (idempotent).

Usage:
    python seed_default_templates.py                    # all schools
    python seed_default_templates.py --school-id <uuid> # single school
"""
import asyncio
import sys

sys.path.insert(0, ".")


async def seed_all():
    import argparse

    parser = argparse.ArgumentParser(description="Seed default templates for schools")
    parser.add_argument("--school-id", dest="school_id", default=None, help="Target a single school by UUID")
    args = parser.parse_args()

    from app.db.session import get_db
    from sqlalchemy import text
    from app.data.default_templates import DEFAULT_DOCUMENT_TEMPLATES, DEFAULT_NOTIFICATION_TEMPLATES

    async for db in get_db():
        # Determine which schools to seed
        if args.school_id:
            result = await db.execute(
                text("SELECT id, name FROM schools WHERE id = :sid"),
                {"sid": args.school_id},
            )
            schools = result.fetchall()
            if not schools:
                print(f"[ERROR] School {args.school_id} not found.")
                break
        else:
            result = await db.execute(text("SELECT id, name FROM schools WHERE is_active = 1"))
            schools = result.fetchall()

        print(f"[INFO] Seeding templates for {len(schools)} school(s)...")

        for school in schools:
            school_id = str(school[0])
            school_name = school[1]
            doc_added = 0
            notif_added = 0

            # ── Document Templates ─────────────────────────────────────────
            for tpl in DEFAULT_DOCUMENT_TEMPLATES:
                existing = await db.execute(
                    text(
                        "SELECT id FROM document_templates "
                        "WHERE school_id = :sid AND template_type = :ttype AND template_name = :tname"
                    ),
                    {"sid": school_id, "ttype": tpl["template_type"], "tname": tpl["template_name"]},
                )
                if existing.fetchone():
                    continue
                await db.execute(
                    text(
                        "INSERT INTO document_templates "
                        "(id, school_id, template_name, template_type, canvas_width_mm, canvas_height_mm, "
                        "template_html, layout_json, is_default, is_active, created_at, updated_at) "
                        "VALUES (NEWID(), :sid, :tname, :ttype, :w, :h, :html, NULL, :is_def, 1, "
                        "GETUTCDATE(), GETUTCDATE())"
                    ),
                    {
                        "sid": school_id,
                        "tname": tpl["template_name"],
                        "ttype": tpl["template_type"],
                        "w": tpl["canvas_width_mm"],
                        "h": tpl["canvas_height_mm"],
                        "html": tpl["template_html"],
                        "is_def": 1 if tpl["is_default"] else 0,
                    },
                )
                doc_added += 1

            await db.commit()

            # ── Notification Templates ─────────────────────────────────────
            for ntpl in DEFAULT_NOTIFICATION_TEMPLATES:
                existing = await db.execute(
                    text(
                        "SELECT id FROM notification_templates "
                        "WHERE school_id = :sid AND event_trigger = :evt AND name = :name"
                    ),
                    {"sid": school_id, "evt": ntpl["event_trigger"], "name": ntpl["name"]},
                )
                if existing.fetchone():
                    continue
                await db.execute(
                    text(
                        "INSERT INTO notification_templates "
                        "(id, school_id, name, channels, event_trigger, subject, body_template, "
                        "is_active, is_default, created_at, updated_at) "
                        "VALUES (NEWID(), :sid, :name, :ch, :evt, :subj, :body, "
                        ":is_active, :is_def, GETUTCDATE(), GETUTCDATE())"
                    ),
                    {
                        "sid": school_id,
                        "name": ntpl["name"],
                        "ch": ntpl["channel"],
                        "evt": ntpl["event_trigger"],
                        "subj": ntpl.get("subject"),
                        "body": ntpl["body_template"],
                        "is_active": 1 if ntpl["is_active"] else 0,
                        "is_def": 1 if ntpl["is_default"] else 0,
                    },
                )
                notif_added += 1

            await db.commit()

            print(
                f"  ✓ {school_name} ({school_id[:8]}…) "
                f"— {doc_added} document template(s), {notif_added} notification template(s) added"
            )

        print("[DONE] Seeding complete.")
        break  # only one DB session needed


asyncio.run(seed_all())
