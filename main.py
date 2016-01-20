import json
import re
import sys
import gspread
import gspread.models
import requests
import slackclient
from xml.etree import ElementTree
from oauth2client.client import SignedJwtAssertionCredentials
from slackclient import SlackClient

class Config(object):
	def __init__(self, filename):
		self.config = json.load(open(filename))

	def __getitem__(self, key):
		return self.config[key]


class RandsChallenges(object):
	def __init__(self, config):
		self._init_client(config)

	def _init_client(self, config):
		json_key = json.load(open(config['credential_file']))
		scope = ['https://spreadsheets.google.com/feeds']

		credentials = SignedJwtAssertionCredentials(json_key['client_email'], json_key['private_key'].encode(), scope)

		gc = gspread.authorize(credentials)

		sheet_id = 'https://spreadsheets.google.com/feeds/spreadsheets/1ouXBKjdgBHQ1okKtt5v6w63sxz5VGT6UT5KXRd3GE9Q'
		sheet_xml_template = '<entry xmlns="http://www.w3.org/2005/Atom"><id>%s</id></entry>'

		sh = gspread.models.Spreadsheet(gc, ElementTree.fromstring(sheet_xml_template % sheet_id))

		self.worksheet = sh.get_worksheet(0)

	def _unpack_cells(self, row_values):
		return row_values[0], row_values[1], row_values[2], row_values[3:]

	def get_all_challenges(self):
		all_challenges = dict()

		print 'total rows', self.worksheet.row_count

		for row_num in range(0, self.worksheet.row_count):
			print 'reading row', row_num
			chal_num, chal_poster, chal_text, values_list = self._unpack_cells(self.worksheet.row_values(row_num + 1))

			if len(chal_num) > 0 and len(chal_poster) > 0 and len(chal_text) > 0:
				#coerce to integer
				chal_num = int(chal_num)

				#first one with a given number wins, sorry
				if chal_num not in all_challenges:
					all_challenges[chal_num] = dict(poster=chal_poster, text=chal_text, row_num=row_num, chal_num=chal_num)
			else:
				#terminate early if we find a row that's totally blank
				if len(chal_num) == 0 and len(chal_poster) == 0 and len(chal_text) == 0:
					break
				else:
					print 'partial row'

		return all_challenges


class SlackInterface(object):
	TOPIC_EXTRACT_EXPR = '^DC([0-9]+).*$'

	def __init__(self, config):
		self.sc = SlackClient(config['slack_token'])
		self.bot_token = config['slackbot_token']
		self.channel_name = config['channel_name']
		self.channel_id = config['channel_id']

	def get_challenge_number_from_topic(self):
		info = json.loads(self.sc.api_call('channels.info', channel=self.channel_id))
		if 'channel' in info and 'topic' in info['channel'] and 'value' in info['channel']['topic']:
			topic = info['channel']['topic']['value']

			print 'got', topic
			match = re.match(SlackInterface.TOPIC_EXTRACT_EXPR, topic)
			if match is None:
				return 0
			else:
				return int(match.group(1))
		else:
			return 0

	def post_to_slack(self, poster_name, challenge_num, challenge):
		print self.sc.api_call('channels.setTopic', channel=self.channel_id, topic='DC%d: %s' % (challenge_num, challenge))
		post_url = 'https://rands-leadership.slack.com/services/hooks/slackbot?token=%s&channel=%%23%s' % (self.bot_token, self.channel_name)
		post_data = ' @%s says: Daily Challenge #%d: %s' % (poster_name, challenge_num, challenge)
		r = requests.post(post_url, data=post_data)
		print r.content



def main():
	if len(sys.argv) < 2:
		print 'syntax: %s filename -- where the filename is a config file' % sys.argv[0]
		sys.exit(1)

	config = Config(sys.argv[1])

	slack = SlackInterface(config)
	chal = RandsChallenges(config)
	all_challenges = chal.get_all_challenges()

	highest_topic = slack.get_challenge_number_from_topic()
	if highest_topic == 0:
		print 'could not get the current topic...'
	else:
		#check if next highest exists
		if (highest_topic + 1) in all_challenges:
			new_challenge = all_challenges[highest_topic + 1]
			slack.post_to_slack(new_challenge['poster'], new_challenge['chal_num'], new_challenge['text'])
		else:
			print 'highest already posted'




if __name__ == '__main__':
	main()

