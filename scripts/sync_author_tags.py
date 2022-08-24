import csv

from stats.models import Author

# to generate author csv file
#
# python manage.py dbshell
#  \copy (select id, email, tag1, tag2, tag3, is_alias, original_id from stats_author) to 'tmp_author.csv' with csv;   # noqa: E501
#

with open("scripts/tmp_author.csv", newline="") as f:
    authors = [
        {
            "id": row[0],
            "email": row[1],
            "tag1": row[2],
            "tag2": row[3],
            "tag3": row[4],
            "original_id": row[6],
        }
        for row in csv.reader(f)
    ]

for author in authors:
    record = Author.objects.filter(email=author["email"]).first()
    if record is None:
        print(f"author {author['email']} not found")
        continue

    record.tag1, record.tag2, record.tag3 = (
        author["tag1"],
        author["tag2"],
        author["tag3"],
    )
    record.save()
