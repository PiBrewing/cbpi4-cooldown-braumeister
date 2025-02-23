import asyncio
import logging
import time
import warnings
from datetime import datetime
from socket import timeout
from typing import KeysView
from scipy.optimize import curve_fit
import pandas as pd
import numpy as np

from cbpi.api import *
from cbpi.api import Property, action, parameters
from cbpi.api.base import CBPiBase
from cbpi.api.config import ConfigType
from cbpi.api.dataclasses import Kettle, NotificationAction, NotificationType, Props
from cbpi.api.step import CBPiStep, StepResult
from cbpi.api.timer import Timer
from voluptuous.schema_builder import message

logger = logging.getLogger(__name__)


@parameters(
    [
        Property.Number(
            label="Temp",
            configurable=True,
            description="Target temperature for cooldown. Notification will be send when temp is reached and Actor can be triggered",
        ),
        Property.Sensor(
            label="Sensor", description="Sensor that is used during cooldown"
        ),
        Property.Actor(
            label="Actor",
            description="Actor can trigger a valve for the cooldwon to target temperature",
        ),
        Property.Kettle(label="Kettle"),
    ]
)
class CooldownStepBM(CBPiStep):

    async def on_timer_done(self, timer):
        self.summary = ""
        if self.actor is not None:
            await self.actor_off(self.actor)
        self.cbpi.notify(
            "CoolDown",
            "Wort cooled down. Please transfer to Fermenter.",
            NotificationType.INFO,
        )
        await self.next()

    async def on_timer_update(self, timer, seconds):
        await self.push_update()

    async def on_start(self):
        try:
            warnings.simplefilter("ignore", np.exceptions.RankWarning)
        except Exception as e:
            logging.error(f"Numpy Error: {e}")
        self.temp_array = []
        self.time_array = []
        self.start_time = time.time()
        self.kettle = self.get_kettle(self.props.get("Kettle", None))
        self.actor = self.props.get("Actor", None)
        self.target_temp = int(self.props.get("Temp", 0))
        self.Interval = (
            10  # Interval in minutes on how often cooldown end time is calculated
        )

        self.cbpi.notify(
            self.name,
            "Cool down to {}°".format(self.target_temp),
            NotificationType.INFO,
        )
        if self.timer is None:
            self.timer = Timer(
                1, on_update=self.on_timer_update, on_done=self.on_timer_done
            )
        self.temp_array.append(
            self.get_sensor_value(self.props.get("Sensor", None)).get("value")
        )
        self.time_array.append(time.time())
        self.next_check = self.start_time + self.Interval * 60
        self.count = 0
        self.initial_date = None

    async def on_stop(self):
        await self.timer.stop()
        self.summary = ""
        if self.actor is not None:
            await self.actor_off(self.actor)
        await self.push_update()

    async def reset(self):
        self.timer = Timer(
            1, on_update=self.on_timer_update, on_done=self.on_timer_done
        )

    async def calculate_time(self, data, target_temp):
        try:
            def func(x, a, c, d):
                return a*np.exp(-c*x)+d
            
            popt, pcov = curve_fit(func, data.index, data.temp, p0=(0, 0.5, 10), maxfev=5000)

            print("Exponential function coefficients:")
            print(popt)

            log_value = (target_temp - popt[2]) if popt[2] < target_temp else 1
            time = ((np.log((log_value) / popt[0])) / -popt[1])*100
            logging.error(f"Time to target: {time} seconds")
            new_time = time + self.start_time

            logging.error(f"Time to reach {target_temp} degrees: {datetime.fromtimestamp(new_time)}")
        except Exception as e:
            logging.error(f"Failed to calculate time: {e}")
            new_time = None
        return new_time

    async def run(self):
        self.start_time = time.time()
        timestring = datetime.fromtimestamp(self.start_time)
        if self.actor is not None:
            await self.actor_on(self.actor)
        self.summary = "Started: {}".format(timestring.strftime("%H:%M"))
        await self.push_update()

        # Wait for prewait time before starting data collection to have the system stabilized with respect to cooldown activity
        logging.error("Waiting for prewait time")
        prewait = 2 # Minutes before data collection starts
        while time.time() < (self.start_time + (prewait * 60)):
            await asyncio.sleep(1)
            
        self.start_time = time.time()
        self.time_array.append(self.start_time)
        current_temp = self.get_sensor_value(self.props.get("Sensor", None)).get(
                "value"
            )
        self.temp_array.append(current_temp)
        
        logging.error("Starting data collection")
        # Start  data collection
        while self.running == True:
            current_temp = self.get_sensor_value(self.props.get("Sensor", None)).get(
                "value"
            )
            if self.count == 3:
                self.temp_array.append(current_temp)
                current_time = time.time()
                if self.initial_date == None:
                    self.initial_date = current_time
                self.time_array.append(current_time)
                self.count = 0
            if time.time() >= self.next_check:
                data = pd.DataFrame({'time': self.time_array, 'temp': self.temp_array})
                data["time"] = pd.to_numeric(data["time"])
                data.set_index("time", inplace=True)
                data.index = pd.to_numeric((data.index-data.index[0]))/100

                self.next_check = time.time() + (self.Interval * 60)

                target_time = await self.calculate_time(data, self.target_temp)
                if target_time is not None:
                    target_timestring = datetime.fromtimestamp(target_time)
                    self.summary = "ECT: {}".format(target_timestring.strftime("%H:%M"))
                    self.cbpi.notify(
                        "Cooldown Step",
                        "Current: {}°, reaching {}° at {}".format(
                            round(current_temp, 1),
                            self.target_temp,
                            target_timestring.strftime("%d.%m %H:%M"),
                        ),
                        NotificationType.INFO,
                    )
                    self.temp_array = []
                    self.time_array = []
                    self.temp_array.append(
                        self.get_sensor_value(self.props.get("Sensor", None)).get("value")
                    )
                    self.start_time = time.time()
                    self.time_array.append(self.start_time)
                    await self.push_update()


            if current_temp <= self.target_temp and self.timer.is_running is not True:
                self.timer.start()
                self.timer.is_running = True

            self.count += 1
            await asyncio.sleep(1)

        return StepResult.DONE

def setup(cbpi):
    """
    This method is called by the server during startup
    Here you need to register your plugins at the server

    :param cbpi: the cbpi core
    :return:
    """
    cbpi.plugin.register("CooldownStepBM", CooldownStepBM)
