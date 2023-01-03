#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `kiara_plugin.streamlit` package."""

import pytest  # noqa

import kiara_plugin.streamlit


def test_assert():

    assert kiara_plugin.streamlit.get_version() is not None
