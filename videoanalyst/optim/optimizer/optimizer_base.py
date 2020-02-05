# -*- coding: utf-8 -*-

import json
import pickle
import tarfile
import time
from abc import ABCMeta, abstractmethod
from typing import List, Dict

import cv2 as cv
import numpy as np

from yacs.config import CfgNode

import torch
from torch import nn
from torch.optim.optimizer import Optimizer

from videoanalyst.utils import Registry

from torch.optim.optimizer import Optimizer

from .optimizer_impl.utils.lr_multiply import multiply_lr, resolve_lr_multiplier_cfg
from .optimizer_impl.utils.freeze import apply_freeze_schedule, resolve_freeze_schedule_cfg
from ..scheduler.scheduler_base import SchedulerBase

TRACK_OPTIMIZERS = Registry('TRACK_OPTIMIZERS')
VOS_OPTIMIZERS = Registry('VOS_OPTIMIZERS')

TASK_OPTIMIZERS = dict(
    track=TRACK_OPTIMIZERS,
    vos=VOS_OPTIMIZERS,
)

class OptimizerBase:
    __metaclass__ = ABCMeta

    r"""
    base class for Sampler. Reponsible for sampling from multiple datasets and forming training pair / sequence.

    Define your hyper-parameters here in your sub-class.
    """
    default_hyper_params = dict()

    def __init__(self, cfg: CfgNode) -> None:
        r"""
        Dataset Sampler, reponsible for sampling from different dataset

        Arguments
        ---------
        cfg: CfgNode
            node name: optimizer

        Internal members
        ----------------
        _model:
            underlying nn.Module
        _optimizer
            underlying optim.optimizer.optimizer_base.OptimizerBase
        _scheduler:
            underlying scheduler
        _param_groups_divider: function
            divide parameter for partial scheduling of learning rate 
            input: nn.Module 
            output: List[Dict], k-v: 'params': nn.Parameter
        
        """
        self._hyper_params = self.default_hyper_params
        self._state = dict()
        self._cfg = cfg
        self._model = None
        self._optimizer = None
        self._scheduler = None
        self._param_groups_divider = None
    
    def set_model(self, model: nn.Module):
        r"""
        Register model to optimize

        Arguments
        ---------
        model: nn.Module
            model to registered in optimizer
        """
        self._model = model

    def build_optimizer(self):
        r"""
        an interface to build optimizer
        """
        if (self._scheduler is not None):
            self._scheduler.set_optimizer(self)

    def set_scheduler(self, scheduler: SchedulerBase):
        r"""
        Set scheduler and register self (optimizer) to scheduler
        Arguments
        ---------
        model: nn.Module
            model to registered in optimizer
        """
        self._scheduler = scheduler

    def get_hps(self) -> dict:
        r"""
        Getter function for hyper-parameters

        Returns
        -------
        dict
            hyper-parameters
        """
        return self._hyper_params

    def set_hps(self, hps: dict) -> None:
        r"""
        Set hyper-parameters

        Arguments
        ---------
        hps: dict
            dict of hyper-parameters, the keys must in self.__hyper_params__
        """
        for key in hps:
            if key not in self._hyper_params:
                raise KeyError
            self._hyper_params[key] = hps[key]
            
    def update_params(self) -> None:
        r"""
        an interface for update params
        """
    def zero_grad(self):
        self._optimizer.zero_grad()

    def step(self):
        self._optimizer.step()

    def state_dict(self):
        self._optimizer.state_dict()

    def schedule(self, epoch: int, iteration: int) -> Dict:
        r"""
        an interface for optimizer scheduling (e.g. adjust learning rate)
        self.set_scheduler need to be called during initialization phase
        """
        schedule_info = dict()
        if self._scheduler is not None:
            schedule_info.update(self._scheduler.schedule(epoch, iteration))

        return schedule_info