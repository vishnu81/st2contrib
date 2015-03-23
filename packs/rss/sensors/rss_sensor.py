import calendar
import hashlib

import feedparser
from six.moves.html_parser import HTMLParser

from st2reactor.sensor.base import PollingSensor

__all__ = [
    'RSSSensor'
]


class HTMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


class RSSSensor(PollingSensor):
    DATASTORE_NAME_SUFFIX = 'last_timestamp'

    def __init__(self, sensor_service, config=None, poll_interval=None):
        super(RSSSensor, self).__init__(sensor_service=sensor_service,
                                        config=config,
                                        poll_interval=poll_interval)

        self._trigger_ref = 'rss.entry'
        self._logger = self._sensor_service.get_logger(__name__)

        config = self._config['sensor']
        self._use_timestamp_filtering = config.get('use_timestamp_filtering', True)

        # Stores a list of monitored feed urls
        self._feed_urls = {}

    def setup(self):
        pass

    def poll(self):
        feed_urls = self._feed_urls.keys()

        self._logger.info('Processing %s feeds' % (len(feed_urls)))

        for feed_url in feed_urls:
            self._logger.info('Processing feed: %s' % (feed_url))
            processed_entries = self._process_feed(feed_url=feed_url)
            self._logger.info('Found and processed %s new entries for feed "%s"' %
                              (processed_entries, feed_url))

    def cleanup(self):
        pass

    def add_trigger(self, trigger):
        if trigger['type'] not in ['rss.feed']:
            return

        feed_url = trigger['parameters']['url']
        self._feed_urls[feed_url] = True

        self._logger.info('Added feed: %s', feed_url)

    def update_trigger(self, trigger):
        pass

    def remove_trigger(self, trigger):
        if trigger['type'] not in ['rss.feed']:
            return

        feed_url = trigger['parameters']['url']
        if feed_url in self._feed_urls:
            del self._feed_urls[feed_url]

        # Clean datastore entries for the removed feed
        name = self._get_datastore_name(feed_url=feed_url)
        self._sensor_service.delete_value(name=name)

        self._logger.info('Removed feed: %s', feed_url)

    def _process_feed(self, feed_url):
        # TODO: Also use etags and last-modified to reduce unncessary downloads
        try:
            parsed = feedparser.parse(feed_url)
        except Exception:
            return

        feed = parsed['feed']
        entries = parsed.get('entries', [])

        # Retrieve timestamp of the last entry (if any)
        if self._use_timestamp_filtering:
            last_entry_timestamp = self._get_last_entry_timestamp(feed_url=feed_url)

        processed_entries_count = 0
        entries_timestamps = []

        for entry in entries:
            entry_timestamp = self._get_entry_timestamp(entry=entry)

            if self._use_timestamp_filtering and entry_timestamp:
                if entry_timestamp <= last_entry_timestamp:
                    # We have already seen this entry, skip it
                    continue

                entries_timestamps.append(entry_timestamp)

            self._dispatch_trigger_for_entry(feed=feed, entry=entry)
            processed_entries_count += 1

        # Store timestamp of the newest entry (if any)
        if self._use_timestamp_filtering and entries_timestamps:
            last_entry_timestamp = max(entries_timestamps)
            self._set_last_entry_timestamp(feed_url=feed_url,
                                           timestamp=last_entry_timestamp)

        return processed_entries_count

    def _get_last_entry_timestamp(self, feed_url):
        name = self._get_datastore_name(feed_url=feed_url)
        timestamp = self._sensor_service.get_value(name=name)

        if timestamp:
            timestamp = int(timestamp)

        return timestamp

    def _set_last_entry_timestamp(self, feed_url, timestamp):
        name = self._get_datastore_name(feed_url=feed_url)

        if timestamp:
            self._sensor_service.set_value(name=name, value=str(timestamp))

        return timestamp

    def _get_datastore_name(self, feed_url):
        """
        Construct datastore name id for the provided feed url.

        :rtype: ``str``
        """
        feed_id = hashlib.md5(feed_url).hexdigest()
        name = '%s.%s' % (feed_id, self.DATASTORE_NAME_SUFFIX)
        return name

    def _get_entry_timestamp(self, entry):
        """
        Retrieve a published / updated timestamp for the provided feed entry.

        By default it tries to use "published" attribute, if this one is not
        available, it falls back to "updated" attribute.
        """
        published_at = entry.get('published_parsed', None)
        updated_at = entry.get('updated_parsed', None)

        if published_at:
            timestamp = calendar.timegm(published_at)
        elif updated_at:
            timestamp = calendar.timegm(updated_at)
        else:
            timestamp = None

        return timestamp

    def _dispatch_trigger_for_entry(self, feed, entry):
        trigger = self._trigger_ref

        feed_title = feed.get('title', None)
        feed_subtitle = feed.get('subtitle', None)
        feed_url = feed.get('link', None)
        feed_updated_at = feed.get('updated_parsed', None)

        if feed_updated_at:
            feed_updated_at = calendar.timegm(feed_updated_at)

        entry_title = entry.get('title', None)
        entry_author = entry.get('author', None)
        entry_url = entry.get('link', None)
        entry_published_at = entry.get('published_parsed', None)
        entry_updated_at = entry.get('updated_parsed', None)
        entry_summary = entry.get('summary', None)
        entry_content = entry.get('content', None)

        if entry_published_at:
            entry_published_at = calendar.timegm(entry_published_at)

        if entry_updated_at:
            entry_updated_at = calendar.timegm(entry_updated_at)

        if entry_content:
            entry_content = entry_content[0].get('value', None)

            stripper = HTMLStripper()
            stripper.feed(entry_content)
            entry_content_raw = stripper.get_data()
        else:
            entry_content_raw = None

        payload = {
            'feed': {
                'title': feed_title,
                'subtitle': feed_subtitle,
                'url': feed_url,
                'feed_updated_at_timestamp': feed_updated_at
            },
            'entry': {
                'title': entry_title,
                'author': entry_author,
                'url': entry_url,
                'published_at_timestamp': entry_published_at,
                'updated_at_timestamp': entry_updated_at,
                'summary': entry_summary,
                'content': entry_content,
                'content_raw': entry_content_raw
            }
        }

        self._sensor_service.dispatch(trigger=trigger, payload=payload)
