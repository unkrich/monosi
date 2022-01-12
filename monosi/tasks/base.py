import abc
from typing import List, Optional
from monosi.events import track_event

from monosi.config.configuration import Configuration
from monosi.project import Project

class TaskBase:
    def __init__(self, args, config):
        self.args = args
        self.config = config

    @classmethod
    def from_args(cls, args):
        try:
            config = Configuration.from_args(args)
        except:
            raise Exception("There was an issue creating the task from args.")

        return cls(args, config)

    @classmethod
    def run_task(cls, *args, **kwargs):
        task = cls(*args)
        return task.run(*args, **kwargs)

    @abc.abstractmethod
    def run(self, *args, **kwargs):
        raise NotImplementedError('Implementation for task does not exist.')

class ProjectTask(TaskBase):
    def __init__(self, args, config):
        super().__init__(args, config)
        self.project: Optional[Project] = None
        self.task_queue: List[TaskBase] = []

    def load_project(self):
        self.project = Project.from_configuration(self.config)
        self.task_queue = self._create_tasks()

    def _initialize(self):
        self.load_project()

    @abc.abstractmethod
    def _create_tasks(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _process_tasks(self):
        raise NotImplementedError

    def run(self):
        self._initialize()
        return self._process_tasks()

class MonitorTask(TaskBase):
    def __init__(self, args, config, monitor):
        super().__init__(args, config)
        self.monitor = monitor

    @classmethod
    def run_task(cls, *args):
        task = cls(*args)
        task.run()

    def run(self):
        self.monitor.run(self.config)

class MonitorsTask(ProjectTask):
    def __init__(self, args, config):
        super().__init__(args, config)
        self.task_queue: List[MonitorTask] = []

    def _create_tasks(self):
        if self.project is None:
            raise Exception("Project was not loaded before running monitors.")

        results = [MonitorTask(self.args, self.config, monitor) for monitor in self.project.monitors]
        track_event(self.config, action="run_finish", label=str(len(self.project.monitors)))
        return results

