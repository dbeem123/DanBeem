# Program positions: how an approved position reaches the site

`data/ct_ltcop_positions.json` holds **approved** positions of the Connecticut Long Term Care Ombudsman Program and nothing else. The repository is public, so drafts never go here. The file ships with `"positions": []`, and the testimony builder then inserts the placeholder `[No approved Program position for this topic. Add one only with State Ombudsman approval.]`.

## Steps
1. **Draft privately.** Write proposed position text in a private document (not this repository, not a branch, not a pull request). Base it on a public record: testimony the Program has submitted, an annual report, or a published statement.
2. **Approval.** The State Long-Term Care Ombudsman approves each position's exact wording and the date.
3. **Publish.** Only after approval, add an entry:
   ```json
   {"id": "staffing-floor-2027", "topic": "staffing_workforce", "threads": ["staffing-floor"],
    "text": "Approved wording, 80 words or fewer.",
    "basis_url": "https://portal.ct.gov/...", "basis_label": "Public record the position rests on",
    "approved_by": "State Long-Term Care Ombudsman", "approved_date": "2027-01-15"}
   ```
4. Run `python scripts/validate_ct_legislative_threads.py`. It refuses any entry without `approved_by`, `approved_date`, `basis_url` or `basis_label`, any text over 80 words, unknown topics or threads, and any key starting with `draft`.
5. To withdraw a position, delete the entry; the builder returns to the placeholder.

## What the site does with it
The testimony builder (`/legislation/#testimony-builder`) shows a matching position as "Position of the Connecticut Long Term Care Ombudsman Program (approved <date>)", with its basis. Storylines, bill lists and the act table never state positions; listing is not a position of the Program.
