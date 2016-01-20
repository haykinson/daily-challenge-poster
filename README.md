To run:

1. virtualenv .venv
2. source .venv/bin/activate
3. pip install -r requirements.txt
4. Set up a project at https://console.developers.google.com, grant access to the Drive API, then create Service Account credentials and save them to the credentials/ subdirectory here.
5. edit sample-config.json and copy to the credentials subdirectory.
6. Run as python main.py path-to-your-config.json

This will grab the full list of daily challenges, compare with the latest topic in the given channel, and then post the next challenge.

TODO
----

- it shouldn't post more than once a day
- make it post on a schedule
- make it more robust
- it should keep trying to post
- should read back the slackbot post we just made, get its link, and call worksheet.update_cell() to populate the cell with the correct =HYPERLINK formula

