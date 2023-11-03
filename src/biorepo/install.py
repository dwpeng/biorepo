import enum
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from typing import List

from rich.progress import Progress, SpinnerColumn, TaskProgressColumn

from . import ui
from .exception import BioReopException
from .shell import Shell
from .source import BaseSource


class RunStatus(enum.Enum):
    SUCCESS = 1
    FAIL = 2
    RUNNING = 3


class Run:
    def __init__(self, shell: Shell, source: BaseSource):
        self.status = RunStatus.RUNNING
        self.shell = shell
        self.source = source

    def run(self, progress: Progress):
        job = progress.add_task(
            f"Installing... [req]{self.source.name}[/]", text="", total=None
        )
        try:
            self.source.create_source()
            self.shell.execute()
            self.status = RunStatus.SUCCESS
            progress.live.console.print(
                f"  [success]{ui.Emoji.SUCC}[/] Install [req]{self.source.name}[/] successful"
            )
        except BioReopException as e:
            self.status = RunStatus.FAIL
            progress.live.console.print(
                f"  [error]{ui.Emoji.FAIL}[/] Install [primary]{self.source.name}[/] failed"
            )
            progress.live.console.print(f"    [error]{e.msg}[/]")
        finally:
            progress.update(job, visible=False)


class Install:
    def __init__(
        self,
        runs: List[Run],
    ):
        self.thread_pool = ThreadPoolExecutor(
            min(
                multiprocessing.cpu_count(),
                len(runs),
            )
        )
        self.runs = runs

    def install(self):
        with ui.UI().make_progress(
            " ",
            SpinnerColumn(ui.SPINNER, speed=1, style="primary"),
            "{task.description}",
            "[info]{task.fields[text]}",
            TaskProgressColumn("[info]{task.percentage:>3.0f}%[/]"),
        ) as progress:
            live = progress.live
            for run in self.runs:
                self.thread_pool.submit(run.run, progress)
            self.thread_pool.shutdown(wait=True)

        failed = [run for run in self.runs if run.status == RunStatus.FAIL]
        if failed:
            live.console.print(
                f"[error]{ui.Emoji.FAIL}[/] Install failed: [primary]{', '.join([run.source.name for run in failed])}[/]"
            )
        else:
            live.console.print(f"{ui.Emoji.POPPER} All complete!")
