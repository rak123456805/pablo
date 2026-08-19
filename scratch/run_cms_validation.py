import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))

from app.database import get_session_factory
from app.services.validator import build_validation_report

async def main():
    factory = get_session_factory()
    async with factory() as session:
        report = await build_validation_report(session)
        print("CMS VALIDATION REPORT SUMMARY:")
        print(f"  Can Publish?   : {report.can_publish}")
        print(f"  Summary        : {report.summary}")
        print(f"  Show Issues    : {len(report.show_issues)}")
        for s in report.show_issues:
            print(f"    Show '{s.show_title}':")
            for issue in s.issues:
                print(f"      - [{issue.severity}] code={issue.code}: {issue.message}")

        print(f"  Episode Issues : {len(report.episode_issues)}")
        for e in report.episode_issues:
            print(f"    Episode '{e.episode_title}' ({e.content_group} / {e.language}):")
            for issue in e.issues:
                print(f"      - [{issue.severity}] code={issue.code}: {issue.message}")

if __name__ == "__main__":
    asyncio.run(main())
