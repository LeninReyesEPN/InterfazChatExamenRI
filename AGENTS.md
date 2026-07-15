<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# UI Typography Rule
- **Primary Font**: Always use **Josefin Sans** for all text elements across the entire web application interface.
- **Tailwind Configuration**: Under no circumstances should the typography be reverted to default sans-serif, system-ui, or Geist fonts. Keep `--font-sans: var(--font-josefin-sans)` active in Tailwind themes.
