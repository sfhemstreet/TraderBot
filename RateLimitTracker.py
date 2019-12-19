import time
from colors import c

class RateLimitTracker:
    """
    Keeps track of time and count so you can avoid hitting an API rate limit.

    Parameters:

    `limit: int`
        max calls ton API per timeframe. default 30

    `timeframe: int`
        timeframe of limit in seconds. default 60
    
    Attributes:

    `limit: int`
        max calls ton API per timeframe. default 30

    `timeframe: int`
        timeframe of limit in seconds. default 60

    `count: int`
        number of calls to API

    `time: int`
        time of last API call in seconds

    Methods:

    `reset`
        manually reset count to 0 and time to current time

    `check`
        checks if ratelimit will be hit, keeps track of count, 
        sleeps if ratelimit will be hit

    `increment`
        use to manually increment count by one

    `set_to_curr_time`
        use to manually set time to current time

    `get_secs_till`
        Get seconds till timeframe elapses from last set time

    """

    def __init__(self, limit=30, timeframe=60):
        self.limit = limit
        self.time = int(time.time())
        self.count = 0
        self.timeframe = timeframe


    def reset(self):
        """Manually reset count to 0 and time to current time."""

        self.time = int(time.time())
        self.count = 0


    def check(self, will_sleep=True, will_increment=True):
        """
        Checks if ratelimit will be hit.
        
        Resets count and time if timeframe has elapsed.

        By default increments count when called. 

        By default will sleep till trimeframe elapses if ratelimit is hit.

        Parameters:

        `will_sleep: boolean`
            if True, will 'sleep' till timeframe limit elapses if rate limit is hit. Default is True

        `will_increment: boolean`
            if True, increments count. Default is True. You may want to set this to false 
            if you aren't 100% sure you will place a trade, 
            but be sure to increment count on your own if you do. 

        Returns:

        `boolean`
            True means you are good. False means you should wait.
            Will always return True with default settings 
            because if you hit the rate limit,
            it will perform a sleep till you are good to make
            another API call. 

        """

        curr_time = int(time.time())
        secs_between = curr_time - self.time
        
        # check if timeframe has elapsed 
        if(secs_between > self.timeframe):
            self.reset()

            if will_increment:
                self.increment()

            return True

        # check if rate limit will be hit
        if(self.count + 1 >= self.limit):
            
            if will_sleep:
                # sleep till we are good, reset, return true
                sleep_time = self.timeframe - secs_between

                print(c[2] + "\nRate Limit Hit, sleeping for " + str(sleep_time) + " seconds.\n" + c[0])

                time.sleep(sleep_time)

                self.reset()

                if will_increment:
                    self.increment()

                return True
            
            else:
                return False


        # we are good, just check if we should increment
        if will_increment:
            self.increment()

        return True

        
    def increment(self):
        """Increments count."""
        self.count = self.count + 1


    def set_to_curr_time(self):
        """sets time to current time."""
        self.time = int(time.time())


    def get_secs_till(self):
        """Get seconds till timeframe elapses from last set time. Can be negative.

        Use this to determine sleep time
        
        Returns:

        `seconds: int`
            seconds till timeframe elapses from last set time. Negative means its passed.
        """
        curr_time = int(time.time())
        secs_between = curr_time - self.time
        secs_till = self.timeframe - secs_between

        return secs_till
