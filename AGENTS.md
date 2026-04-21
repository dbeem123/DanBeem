# Agent Rules for This Repository

- Use JSON files in `/data` as the source of truth for templates, validation rules, keyword maps, and reference indexes.
- Do not hardcode duplicate copies of these rules in UI components if a `/data` file exists.
- Prefer reusing a shared data loader for `/data` files.
