from django.contrib import admin
from django.utils.html import format_html

from .models import Bundle, Category, Genre, Instrument, SheetMusic
from .utils.pdf_processing import generate_cover_thumbnail, generate_watermarked_preview


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('display_order', 'name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'slug', 'parent', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('parent__name', 'display_order', 'name')
    raw_id_fields = ('parent',)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'family', 'slug', 'display_order')
    list_filter = ('family',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('family', 'display_order', 'name')


@admin.register(SheetMusic)
class SheetMusicAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'composer', 'year_published', 'decade',
        'price', 'is_active', 'featured', 'cover_preview',
    )
    list_filter = ('is_active', 'featured', 'decade', 'genres', 'ensemble_type')
    search_fields = ('title', 'composer', 'lyricist', 'publisher', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('genres', 'categories', 'instruments')
    readonly_fields = ('decade', 'preview_image', 'preview_pdf', 'cover_preview', 'created_at', 'updated_at')
    save_on_top = True

    fieldsets = (
        ('Identity', {
            'fields': ('title', 'slug', 'is_active', 'featured'),
        }),
        ('Creators', {
            'fields': ('composer', 'lyricist', 'arranger'),
        }),
        ('Publication', {
            'fields': ('publisher', 'year_published', 'decade'),
        }),
        ('Classification', {
            'fields': ('genres', 'categories', 'instruments', 'ensemble_type'),
        }),
        ('Description', {
            'fields': ('description', 'condition_notes'),
        }),
        ('Pricing', {
            'fields': ('price',),
        }),
        ('Files', {
            'fields': ('pdf_file', 'cover_image', 'cover_preview', 'audio_sample', 'page_count'),
            'description': 'Upload the full PDF. Cover thumbnail and watermarked preview are auto-generated.',
        }),
        ('Auto-Generated Previews', {
            'fields': ('preview_image', 'preview_pdf'),
            'classes': ('collapse',),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def cover_preview(self, obj):
        if obj.cover_image:
            return format_html(
                '<img src="{}" style="height:80px;width:auto;border-radius:4px;" />',
                obj.cover_image.url,
            )
        if obj.preview_image:
            return format_html(
                '<img src="{}" style="height:80px;width:auto;border-radius:4px;" />',
                obj.preview_image.url,
            )
        return '—'
    cover_preview.short_description = 'Preview'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._generate_previews(obj)

    def _generate_previews(self, obj):
        if not obj.pdf_file:
            return
        pdf_path = obj.pdf_file.path

        # Cover thumbnail
        if not obj.cover_image:
            thumbnail = generate_cover_thumbnail(pdf_path)
            if thumbnail:
                obj.cover_image.save(f'{obj.slug}-cover.webp', thumbnail, save=False)

        # Always regenerate preview image and preview PDF from the full PDF
        preview_img = generate_cover_thumbnail(pdf_path, width=800)
        if preview_img:
            obj.preview_image.save(f'{obj.slug}-preview.webp', preview_img, save=False)

        watermarked = generate_watermarked_preview(pdf_path, obj.slug)
        if watermarked:
            obj.preview_pdf.save(f'{obj.slug}-preview.pdf', watermarked, save=False)

        obj.save()


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'piece_count', 'is_active', 'featured')
    list_filter = ('is_active', 'featured')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('items',)
    readonly_fields = ('created_at', 'updated_at')

    def piece_count(self, obj):
        return obj.items.count()
    piece_count.short_description = 'Pieces'
