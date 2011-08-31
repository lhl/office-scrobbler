#!/usr/bin/env python


import json
import os
import pylast
import subprocess
import sys
import time


def main():
  # Get Settings
  SETTINGS_FILE = os.path.abspath(os.path.dirname(sys.argv[0])) + '/settings'
  s = json.load(open(SETTINGS_FILE))

  # Get Lastcheck
  LC_FILE = os.path.abspath(os.path.dirname(sys.argv[0])) + '/lastcheck'
  lastcheck = os.stat(LC_FILE).st_mtime


  ### Mac OS X Idle Time
  '''
  adapted from Perl one-liner by Jeremy Nixon
  http://www.dssw.co.uk/sleepcentre/threads/system_idle_time_how_to_retrieve.html
  timing the perl, it actually runs slightly faster, but it's not worth optimizing
  '''
  for line in reversed(subprocess.check_output(['/usr/sbin/ioreg', '-c', 'IOHIDSystem']).split('\n')):
    if line.find('Idle') > -1:
      idle = int(line.split()[-1])/1000000000.0

      if idle > s['idle']:
        touch(LC_FILE)
        sys.exit()
      else:
        break


  ### Still here? OK, let's do this...

  lastfm = pylast.LastFMNetwork(api_key = s['api_key'], 
                                api_secret = s['api_secret'], 
                                username = s['user'], 
                                password_hash = s['pw'])

  follow_user = pylast.User(s['follow_user'], lastfm)

  # Set Now Playing
  np = follow_user.get_now_playing()
  if np:
    mynp = pylast.User(s['user'], lastfm).get_now_playing()
    if mynp and mynp.get_artist() == np.get_artist() and \
       mynp.get_title() == np.get_title():
      # print 'already playing'
      pass
    else:
      # Scrobble Now Playing Track
      # print np
      lastfm.update_now_playing(np.get_artist(),
                                np.get_title(),
                                np.get_album(),
                                duration=np.get_duration(),
                                mbid=np.get_mbid())


  # Scrobble Track
  '''
  There's a race condition here. I'm erring on the side of avoiding dupes even if there's the slight chance you could miss a song submission. You could probably do some smart dupe-checking instead, but that's a PITA.
  '''
  played_tracks = follow_user.get_recent_tracks()
  current = time.time()
  touch(LC_FILE) # if updates fail, tough noogies


  if(len(played_tracks)):
    for pt in played_tracks:
      if int(pt.timestamp) > lastcheck:
        # print pt
        # print pt.track.get_artist()
        # print pt.track.get_title()
        # print pt.track.get_album()
        # print pt.timestamp
        # print

        lastfm.scrobble(pt.track.get_artist(),
                        pt.track.get_title(),
                        pt.timestamp,
                        pt.track.get_album(),
                        duration=pt.track.get_duration(),
                        mbid=pt.track.get_mbid())

      '''
      We use the idle time as a rough sanity check - we only submit the last song if say your computer just woke up from sleep or something.
      '''
      if current-lastcheck > s['idle']:
        break


# http://stackoverflow.com/questions/1158076/implement-touch-using-python
def touch(fname, times = None):
    with file(fname, 'a'):
            os.utime(fname, times)


if __name__ == "__main__":
  main()
