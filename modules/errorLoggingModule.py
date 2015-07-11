from ircBase import *
import ConfigParser
import urllib, urllib2
import json
import re

config = ConfigParser.SafeConfigParser()
config.read('configs/errorLoggingModule.conf')

GITHUB_API_URL = 'https://api.github.com'
GITHUB_API_TOKEN =config.get('Github', 'api_token')
GITHUB_REPO = config.get('Github', 'repo')
GITHUB_USER = config.get('Github', 'username')

_last_reported_issue = {'title': '', 'issue': ''}

@respondtoregex('(error|err) (me|ma)(.*)')
def logging_response(message, **extra_args):
  """Private message the details of the last error."""
  last_log_error_title = get_last_log_error_title()
  last_saved_error_title = _last_reported_issue['title']

  if (last_log_error_title != last_saved_error_title):
    github_issue = find_github_issue(last_log_error_title)

    if github_issue:
      save_last_reported_issue(last_log_error_title, github_issue)
    else:
      new_issue = create_github_issue(last_log_error_title, get_last_log_error_body())
      new_issue = new_issue if new_issue else "Go fuck yourself"
      save_last_reported_issue(last_log_error_title, new_issue)

  return_messages = [IrcMessage.new_private_message(_last_reported_issue['title'], message.sending_nick)]
  return_messages.append(IrcMessage.new_private_message("For more information: " + _last_reported_issue['issue'], message.sending_nick))
  return  return_messages

def save_last_reported_issue(issue_title, issue):
  """Saves an issue into memory for use later."""
  _last_reported_issue['title'] = issue_title
  _last_reported_issue['issue'] = issue

def get_last_log_error_title():
  """Get the exact line that casued the last error in the log file and return it."""
  with open('modules.log') as f:
    content = f.readlines()

    #Third line from the bottom of the error log is always the title of the last error
    return content[-3]

def get_last_log_error_body():
  """Get the entire stack trace of the last error in the log file and return it."""
  with open('modules.log') as f:
    content = f.readlines()
    error_indexes = [i for i, line in enumerate(content) if re.search('ERROR:.*:.*', line)]
    return ''.join(content[error_indexes[-1]:])

def find_github_issue(issue_title):
  """Find a github issue in RafiBot repo with the given title and return its url."""

  #Make API request to get a list of issues
  request = urllib2.Request("%s/repos/%s/%s/issues" % (GITHUB_API_URL, GITHUB_USER, GITHUB_REPO))
  request.add_header("Authorization", "token %s" % GITHUB_API_TOKEN)   
  response = urllib2.urlopen(request)
  parsed_json = json.loads(response.read())

  #Find and return issue URL
  matching_issues = [json_issue['html_url'] for json_issue in parsed_json if json_issue['title'] == issue_title]
  return None if len(matching_issues) == 0 else matching_issues[0]

def create_github_issue(issue_title, issue_body):
  """Create a new issue in RafiBot repo with the given title and body and return its url."""

  #Create the post body for the issue
  post_data = json.dumps({
    'title': issue_title,
    'body': issue_body
  })

  #Make API request to create the new issue
  request = urllib2.Request("%s/repos/%s/%s/issues" % (GITHUB_API_URL, GITHUB_USER, GITHUB_REPO), post_data)
  request.add_header("Authorization", "token %s" % GITHUB_API_TOKEN)   
  response = urllib2.urlopen(request)
  parsed_json = json.loads(response.read())

  return None if response.getcode() != 201 else parsed_json['html_url']
