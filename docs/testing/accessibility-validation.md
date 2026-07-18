# Accessibility validation

The action dialog uses an accessible name and description, `aria-modal`, initial focus, a contained
Tab sequence, Escape dismissal when safe, focus restoration, native form validation, visible error
messages, and a visually distinct destructive action. The proposed-revision form uses labelled
native controls and a stacked responsive layout. Component tests exercise dialog naming, focus,
keyboard submission, and restoration.

Automated page scans and manual browser review were blocked at this checkpoint because the Docker
application environment was unavailable. Before beta, run axe or an equivalent scanner on public
resource, correction, sign-in, queue, correction detail, and re-verification editor pages. Then
manually check keyboard-only completion, VoiceOver names/state/errors, 200% zoom, narrow mobile
layout, high contrast, reduced motion, and reduced transparency. Automated scans supplement rather
than replace those checks.
