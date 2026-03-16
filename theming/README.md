# Dynamic Event Theming System

The Dynamic Event Theming System automatically extracts colors from event logos and banners to create custom branded themes that are applied consistently across all three portals (Staff, Participant, Organizer).

## Features

- **Automatic Color Extraction**: Extracts dominant colors from event brand assets
- **WCAG Compliance**: Ensures all generated themes meet accessibility standards
- **Multi-Portal Consistency**: Applies themes uniformly across all portals
- **Performance Optimization**: Multi-level caching system for fast theme delivery
- **Fallback System**: Professional default themes when extraction fails
- **Theme Variations**: Support for light/dark modes and other variations

## Models

### EventTheme
Main theme model containing color palette and generated CSS for each event.

### ColorPalette
Stores extracted colors from brand assets with confidence scores and metadata.

### ThemeVariation
Different variations of a theme (light/dark, high contrast, etc.).

### ThemeCache
Performance optimization cache for generated themes.

### ThemeGenerationLog
Audit log for all theme generation activities.

## Usage

### Admin Interface
Access the Django admin to manage themes:
- View and edit event themes
- Monitor theme generation logs
- Manage cache entries
- View color palettes

### Management Commands

Generate themes for events:
```bash
# Generate themes for all events without themes
python manage.py generate_themes

# Generate theme for specific event
python manage.py generate_themes --event-id 123

# Force regenerate all themes
python manage.py generate_themes --force

# Dry run to see what would be done
python manage.py generate_themes --dry-run
```

### API Endpoints

- `GET /theming/` - List all themes
- `GET /theming/event/{event_id}/` - Get theme for specific event
- `POST /theming/event/{event_id}/generate/` - Generate/regenerate theme
- `GET /theming/event/{event_id}/preview/{portal_type}/` - Preview theme CSS
- `POST /theming/event/{event_id}/extract-colors/` - Extract colors from image

### Views

- **Theme List**: View all themes for user's events
- **Event Theme Detail**: Detailed view of theme with color palette and statistics
- **Theme Preview**: Preview how theme looks for different portals
- **Color Extraction**: Extract colors from uploaded brand assets

## Installation

1. Add `'theming'` to `INSTALLED_APPS` in settings.py
2. Run migrations: `python manage.py migrate`
3. Include theming URLs in main urls.py: `path('theming/', include('theming.urls'))`

## Testing

Run the test suite:
```bash
python manage.py test theming
```

The test suite includes:
- Model functionality tests
- View integration tests
- API endpoint tests
- Color extraction tests
- Cache behavior tests

## Architecture

The system follows a modular architecture with clear separation of concerns:

- **Theme Engine**: Central orchestrator for theme generation
- **Color Extractor**: Analyzes brand assets to extract color palettes
- **Theme Generator**: Converts color palettes into complete CSS themes
- **Accessibility Validator**: Ensures WCAG compliance
- **Portal Renderer**: Applies themes consistently across portals
- **Cache Manager**: Optimizes performance with multi-level caching
- **Fallback Manager**: Provides professional defaults when needed

## Future Enhancements

- Real color extraction using computer vision libraries
- Advanced accessibility features
- Theme customization interface
- Bulk theme operations
- Theme analytics and insights
- Integration with external design tools

## Contributing

When contributing to the theming system:

1. Follow the existing code style and patterns
2. Add tests for new functionality
3. Update documentation as needed
4. Ensure WCAG compliance for any UI changes
5. Test across all three portals (Staff, Participant, Organizer)

## Security Considerations

- All uploaded images are validated and sanitized
- CSS content is validated to prevent injection attacks
- Access control ensures users can only modify their own event themes
- Audit logging tracks all theme-related activities