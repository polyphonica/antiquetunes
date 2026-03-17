"""
Management command to seed genres, categories, and instruments.
Safe to run multiple times — uses get_or_create throughout.

Usage:
    python manage.py seed
    python manage.py seed --genres --instruments   # selective
"""

from django.core.management.base import BaseCommand
from apps.catalogue.models import Category, Genre, Instrument


GENRES = [
    {'name': 'Ragtime',       'display_order': 1, 'description': 'Syncopated piano and ensemble music popular from the 1890s to 1910s.'},
    {'name': 'Jazz',          'display_order': 2, 'description': 'America\'s original art form — improvisation, swing, and blues harmony.'},
    {'name': 'Blues',         'display_order': 3, 'description': 'Roots music of the American South, foundational to jazz and rock.'},
    {'name': 'Tin Pan Alley', 'display_order': 4, 'description': 'The commercial popular song industry centred in New York, 1890s–1950s.'},
    {'name': 'March',         'display_order': 5, 'description': 'Military and ceremonial march music, popularised by John Philip Sousa.'},
    {'name': 'Waltz',         'display_order': 6, 'description': 'Three-quarter time dance music from the ballrooms of Europe and America.'},
    {'name': 'Fox Trot',      'display_order': 7, 'description': 'A smooth, progressive ballroom dance popular from the 1910s onward.'},
    {'name': 'Novelty',       'display_order': 8, 'description': 'Humorous or technically flashy popular piano pieces of the 1920s.'},
    {'name': 'Gospel',        'display_order': 9, 'description': 'Devotional and spiritual music rooted in African American church tradition.'},
    {'name': 'Vaudeville',    'display_order': 10, 'description': 'Songs and sketches from the American variety theatre tradition.'},
]

# Categories: (name, parent_name or None, display_order)
CATEGORIES = [
    # Top-level
    ('Vocal',         None,      1),
    ('Instrumental',  None,      2),
    ('Orchestral',    None,      3),
    # Vocal children
    ('Solo Voice',    'Vocal',   1),
    ('Voice & Piano', 'Vocal',   2),
    ('Duet',          'Vocal',   3),
    ('Choir / Glee',  'Vocal',   4),
    # Instrumental children
    ('Piano Solo',    'Instrumental', 1),
    ('Piano Duet',    'Instrumental', 2),
    ('Guitar',        'Instrumental', 3),
    ('Violin',        'Instrumental', 4),
    ('Band',          'Instrumental', 5),
    # Orchestral children
    ('Full Orchestra',   'Orchestral', 1),
    ('Chamber Music',    'Orchestral', 2),
    ('Dance Orchestra',  'Orchestral', 3),
]

# Instruments: (name, family, display_order)
INSTRUMENTS = [
    # Keyboard
    ('Piano',       'keyboard', 1),
    ('Organ',       'keyboard', 2),
    ('Accordion',   'keyboard', 3),
    ('Harmonium',   'keyboard', 4),
    # Strings
    ('Violin',      'strings',  1),
    ('Viola',       'strings',  2),
    ('Cello',       'strings',  3),
    ('Double Bass', 'strings',  4),
    ('Banjo',       'strings',  5),
    ('Guitar',      'strings',  6),
    ('Ukulele',     'strings',  7),
    ('Mandolin',    'strings',  8),
    # Woodwind
    ('Flute',       'woodwind', 1),
    ('Clarinet',    'woodwind', 2),
    ('Oboe',        'woodwind', 3),
    ('Bassoon',     'woodwind', 4),
    ('Saxophone',   'woodwind', 5),
    ('Piccolo',     'woodwind', 6),
    # Brass
    ('Trumpet',     'brass',    1),
    ('Cornet',      'brass',    2),
    ('Trombone',    'brass',    3),
    ('French Horn', 'brass',    4),
    ('Tuba',        'brass',    5),
    # Percussion
    ('Drums',       'percussion', 1),
    ('Xylophone',   'percussion', 2),
    ('Timpani',     'percussion', 3),
    # Voice
    ('Soprano',             'voice', 1),
    ('Mezzo-Soprano',       'voice', 2),
    ('Alto',                'voice', 3),
    ('Tenor',               'voice', 4),
    ('Baritone',            'voice', 5),
    ('Bass',                'voice', 6),
    ('Unspecified Voice',   'voice', 7),
    # Ensemble
    ('Full Orchestra',  'ensemble', 1),
    ('Band',            'ensemble', 2),
    ('Ensemble',        'ensemble', 3),
]


class Command(BaseCommand):
    help = 'Seed genres, categories, and instruments'

    def add_arguments(self, parser):
        parser.add_argument('--genres',      action='store_true', help='Seed only genres')
        parser.add_argument('--categories',  action='store_true', help='Seed only categories')
        parser.add_argument('--instruments', action='store_true', help='Seed only instruments')

    def handle(self, *args, **options):
        selective = options['genres'] or options['categories'] or options['instruments']
        do_all = not selective

        if do_all or options['genres']:
            self._seed_genres()
        if do_all or options['categories']:
            self._seed_categories()
        if do_all or options['instruments']:
            self._seed_instruments()

        self.stdout.write(self.style.SUCCESS('Seeding complete.'))

    def _seed_genres(self):
        created = 0
        for data in GENRES:
            _, is_new = Genre.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description':   data['description'],
                    'display_order': data['display_order'],
                }
            )
            if is_new:
                created += 1
        self.stdout.write(f'  Genres:      {created} created, {len(GENRES) - created} already existed')

    def _seed_categories(self):
        created = 0
        # Two passes: parents first, then children
        for name, parent_name, order in CATEGORIES:
            parent = Category.objects.filter(name=parent_name).first() if parent_name else None
            _, is_new = Category.objects.get_or_create(
                name=name,
                parent=parent,
                defaults={'display_order': order}
            )
            if is_new:
                created += 1
        self.stdout.write(f'  Categories:  {created} created, {len(CATEGORIES) - created} already existed')

    def _seed_instruments(self):
        created = 0
        for name, family, order in INSTRUMENTS:
            _, is_new = Instrument.objects.get_or_create(
                name=name,
                defaults={'family': family, 'display_order': order}
            )
            if is_new:
                created += 1
        self.stdout.write(f'  Instruments: {created} created, {len(INSTRUMENTS) - created} already existed')
