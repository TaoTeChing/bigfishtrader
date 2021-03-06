from datetime import datetime

from fxdayu.data.base import AbstractDataSupport
import pandas as pd
from numpy import float64


class PanelDataSupport(AbstractDataSupport):
    def __init__(self, panel, context=None, side="L", frequency='D'):
        """
        Create a PannelDataSupport with a pandas.Panel object.
        Panel's inner data can be accessed using method history() and current()
        context is a optional parameters, to

        Args:
            panel(pandas.Panel): Panel where real data stored in
            context: default end bar number refer to context.real_bar_num
            side(str): "L" or "R", "L" means bar's datetime refer to it's start time
                "R" means bar's datetime refer to it's end time
        """
        super(PanelDataSupport, self).__init__()
        self._panel = panel
        self._frequency = frequency
        self._others = {}
        self._date_index = self._panel.iloc[0].index
        self._side = side
        self._context = context

    @property
    def date_index(self):
        """
        Panel's datetime index, that is to it's major axis, which contains datetime of
        all the bars in panel.

        Returns:
            pandas.DatetimeIndex: Panel's datetime index
        """
        return self._date_index

    def set_context(self, context):
        """
        set the context

        Args:
            context:

        Returns:
            None
        """
        self._context = context

    def instance(self, tickers, fields, frequency, start=None, end=None, length=None):
        pass

    def _get_ending_index(self, end):
        if isinstance(end, int):
            return end  # ending bar's number (start from 1) was given
        elif isinstance(end, datetime):
            # ending bar's datetime was given
            return self._date_index.searchsorted(end, side=self._side)
        else:
            raise TypeError()

    def _get_starting_index(self, start):
        if isinstance(start, int):
            return start - 1  # starting bar's number (start from 1) was given
        elif isinstance(start, datetime):
            # starting bar's datetime was given
            return self._date_index.searchsorted(start, side=self._side)
        else:
            raise TypeError()

    def history(self, tickers, fields, frequency, start=None, end=None, length=None):
        """


        Args:
            tickers:
            fields:
            frequency:
            start:
            end:
            length:

        Returns:

        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if isinstance(fields, str):
            fields = [fields]
        if frequency == self._frequency:
            if start:
                start_index = self._get_starting_index(start)
                if end:
                    end_index = self._get_ending_index(end)
                elif length:
                    end_index = start_index + length
                else:
                    end_index = self._context.real_bar_num  # using current bar number in context
            else:
                if end:
                    end_index = self._get_ending_index(end)
                else:
                    end_index = self._context.real_bar_num  # using current bar number in context
                start_index = end_index - length
            if len(tickers) == 1:
                df = self._panel[tickers[0]].iloc[start_index:end_index]
                if fields:
                    if len(fields) == 1:
                        return df[fields[0]]
                    else:
                        return df[fields]
                else:
                    return df
            else:
                panel = self._panel[tickers].iloc[:, start_index:end_index]
                if fields:
                    if len(fields) == 1:
                        return panel.loc[:, :, fields[0]]
                    else:
                        # TODO whether it is necessary to set copy=False
                        return panel.loc[:, :, fields].swapaxes(0, 2)
                else:
                    return panel.swapaxes(0, 2)
        else:
            pn = self._others[frequency]

    def current(self, tickers, fields=None):
        """

        Args:
            tickers:
            fields:

        Returns:

        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if isinstance(fields, str):
            fields = [fields]
        if len(tickers) == 1:
            series = self._panel[tickers[0]].iloc[self._context.real_bar_num - 1]
            if fields:
                if len(fields) == 1:
                    return series[fields[0]]
                else:
                    return series[fields]
            else:
                return series
        else:
            df = self._panel[tickers].iloc[:, self._context.real_bar_num - 1].T
            if fields:
                if len(fields) == 1:
                    return df[fields[0]]
                else:
                    return df[fields]
            else:
                return df

    def pop(self, item):
        return self._panel.pop(item)

    def insert(self, item, frame, frequency=None):
        if not frequency or frequency == self._frequency:
            self._panel[item] = frame
        else:
            self._others.setdefault(frequency, pd.Panel())[item] = frame


class Context(object):
    @property
    def current_time(self):
        return datetime.now()


class MultiPanelData(AbstractDataSupport):
    def __init__(self, engine, context=None):
        super(MultiPanelData, self).__init__(engine)
        self._panels = {}
        self._frequency = None
        self.major_axis = None
        self.context = context if context is not None else Context()

    def set_context(self, context):
        self.context = context

    def init(self, frequency, **ticker_frame):
        panel = self.insert(frequency, **ticker_frame)
        self._frequency = frequency
        self.major_axis = panel.major_axis

    def insert(self, frequency, **ticker_frame):
        panel = self._panels.get(frequency, None)
        if panel is not None:
            for ticker, frame in ticker_frame.items():
                panel[ticker] = frame

        else:
            panel = pd.Panel.from_dict(ticker_frame)
            self._panels[frequency] = panel
        return panel

    def drop(self, frequency, *tickers):
        panel = self._panels.get(frequency, None)
        if panel is not None:
            if len(tickers):
                for ticker in tickers:
                    panel.pop(ticker)
            else:
                self._panels.pop(frequency)

    @staticmethod
    def _find(panel, item, major, minor):
        if item is not None:
            if isinstance(item, (str, unicode)):
                frame = panel[item]
                return frame[minor].iloc[major]
            else:
                panel = panel[item]
                return panel[:, major, minor]
        else:
            if len(panel.items) == 1:
                return panel[panel.items[0]][minor].iloc[major]
            else:
                return panel[:, major, minor]

    @staticmethod
    def search_axis(axis, time):
        index = axis.searchsorted(time)
        if axis[index] <= time:
            return index
        else:
            return index - 1

    def major_slice(self, axis, now, start, end, length):
        last = self.search_axis(axis, now)

        if end:
            end = self.search_axis(axis, end)
            if end > last:
                end = last
        else:
            end = last

        if start:
            start = axis.searchsorted(pd.to_datetime(start))
            if length:
                if start + length <= end+1:
                    return slice(start, start+length)
                else:
                    return slice(start, end+1)
            else:
                return slice(start, end+1)
        elif length:
            end += 1
            return slice(end-length if end > length else 0, end)
        else:
            return slice(0, end+1)

    def current(self, tickers, fields=None):
        if fields is None:
            fields = slice(None)
        panel = self._panels[self._frequency]
        end = pd.to_datetime(self.context.current_time)
        index = panel.major_axis.searchsorted(end, 'left')
        if index >= len(panel.major_axis):
            index = -1

        if isinstance(tickers, (str, unicode)):
            frame = panel[tickers]
            return frame[fields].iloc[index]
        else:
            for ticker in tickers:
                if ticker not in panel.items:
                    raise KeyError('%s not in items' % ticker)
            panel = panel[tickers]
            return panel.iloc[:, index].T[fields]

    def history(
            self, tickers, frequency, fields=None,
            start=None, end=None, length=None
    ):
        if fields is None:
            fields = slice(None)
        panel = self._panels[frequency]
        index_slice = self.major_slice(panel.major_axis, self.current_time, start, end, length)
        return self._find(panel, tickers, index_slice, fields)

    @property
    def frequency(self):
        return self._frequency

    @property
    def current_time(self):
        return self.context.current_time
