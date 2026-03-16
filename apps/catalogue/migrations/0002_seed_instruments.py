from django.db import migrations


INSTRUMENTS = [
    # (name, family)
    ('Piano', 'keyboard'),
    ('Organ', 'keyboard'),
    ('Accordion', 'keyboard'),
    ('Harmonium', 'keyboard'),
    ('Violin', 'strings'),
    ('Viola', 'strings'),
    ('Cello', 'strings'),
    ('Double Bass', 'strings'),
    ('Banjo', 'strings'),
    ('Guitar', 'strings'),
    ('Ukulele', 'strings'),
    ('Mandolin', 'strings'),
    ('Harp', 'strings'),
    ('Flute', 'woodwind'),
    ('Piccolo', 'woodwind'),
    ('Clarinet', 'woodwind'),
    ('Bass Clarinet', 'woodwind'),
    ('Oboe', 'woodwind'),
    ('Bassoon', 'woodwind'),
    ('Saxophone', 'woodwind'),
    ('Alto Saxophone', 'woodwind'),
    ('Tenor Saxophone', 'woodwind'),
    ('Trumpet', 'brass'),
    ('Cornet', 'brass'),
    ('Trombone', 'brass'),
    ('French Horn', 'brass'),
    ('Tuba', 'brass'),
    ('Euphonium', 'brass'),
    ('Drums', 'percussion'),
    ('Xylophone', 'percussion'),
    ('Timpani', 'percussion'),
    ('Voice (Soprano)', 'voice'),
    ('Voice (Mezzo-Soprano)', 'voice'),
    ('Voice (Alto)', 'voice'),
    ('Voice (Tenor)', 'voice'),
    ('Voice (Baritone)', 'voice'),
    ('Voice (Bass)', 'voice'),
    ('Voice (Unspecified)', 'voice'),
    ('Full Orchestra', 'ensemble'),
    ('Concert Band', 'ensemble'),
    ('String Quartet', 'ensemble'),
    ('Piano Trio', 'ensemble'),
]

GENRES = [
    ('Ragtime', 0),
    ('Jazz', 1),
    ('Blues', 2),
    ('Tin Pan Alley', 3),
    ('March', 4),
    ('Waltz', 5),
    ('Ballad', 6),
    ('Novelty', 7),
    ('Musical Theatre', 8),
    ('Classical', 9),
]


def seed_data(apps, schema_editor):
    Instrument = apps.get_model('catalogue', 'Instrument')
    Genre = apps.get_model('catalogue', 'Genre')

    from django.utils.text import slugify
    for i, (name, family) in enumerate(INSTRUMENTS):
        Instrument.objects.get_or_create(
            name=name,
            defaults={'slug': slugify(name), 'family': family, 'display_order': i}
        )

    for order, (name, display_order) in enumerate(GENRES):
        Genre.objects.get_or_create(
            name=name,
            defaults={'slug': slugify(name), 'display_order': display_order}
        )


def unseed_data(apps, schema_editor):
    pass  # Leave data in place on reverse


class Migration(migrations.Migration):

    dependencies = [
        ('catalogue', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_data, unseed_data),
    ]
