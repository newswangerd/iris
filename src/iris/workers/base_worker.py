from torch import multiprocessing as mp


class IRISWorker:
    @classmethod
    def _start(cls, *args, worker_intialized=None, **kwargs):
        worker = cls(*args, **kwargs)

        if worker_intialized:
            worker_intialized.set()
        try:
            worker._run()
        except KeyboardInterrupt:
            return

    def _run(self) -> None:
        raise NotImplemented

    @classmethod
    def start_process(cls, *args, **kwargs):
        proc = mp.Process(target=cls._start, args=args, kwargs=kwargs)
        proc.start()
        return proc
