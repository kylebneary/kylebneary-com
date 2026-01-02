# Antigravity Personas

This directory contains "Persona" definitions for the Antigravity agent. These files define specific roles, responsibilities, and styles to help the agent provide more targeted and effective assistance.

## Available Personas

- **[Flask Developer](flask_developer.md)**: Expert in Flask, SQLAlchemy, Jinja2, and web app architecture.
- **[Python Project Developer](python_project_developer.md)**: Expert in general Python scripting, tooling, packaging, and testing.
- **[Blog Writer](blog_writer.md)**: Specialized in writing engaging, SEO-friendly technical content in Markdown.
- **[Orchestrator](orchestrator.md)**: Project manager focused on task tracking, planning, and high-level architecture.

## How to Use

To switch the agent into a specific persona, simply ask:

> "Act as the **Flask Developer**."
> "Switch to **Blog Writer** mode."
> "I need the **Orchestrator** to review the plan."

Or, you can explicitly point the agent to these files:

> "Please review this code following the guidelines in `.agent/personas/python_project_developer.md`."

## Tips for Effectiveness

1.  **Context Switching**: When changing tasks (e.g., from coding backend to writing a blog post), explicitly ask the agent to switch personas. This resets the "mindset".
2.  **Orchestration**: Use the Orchestrator to plan complex features before diving into code.
3.  **Refining Personas**: Feel free to edit these `.md` files to add specific rules (e.g., "Always use f-strings" or "Prefer 'We' over 'I' in blogs").
