from unittest.mock import Mock

import pytest

from tinygrad.runtime.autogen import pci
from tinygrad.runtime.support.nv.nvdev import NVDev
from tinygrad.runtime.support.system import APLRemotePCIDevice


def fake_nvdev(pci_dev, wpr2):
  dev = object.__new__(NVDev)
  dev.pci_dev, dev.devfmt = pci_dev, "usb4"
  dev.reg = lambda _: Mock(read=Mock(return_value=wpr2))
  return dev


def test_tinygpu_wpr2_fails_before_reset(monkeypatch):
  monkeypatch.delenv("TINYGPU_FORCE_RESET", raising=False)
  pci_dev = object.__new__(APLRemotePCIDevice)
  pci_dev.read_config, pci_dev.write_config_flush, pci_dev.reset = Mock(), Mock(), Mock()

  with pytest.raises(RuntimeError, match="TinyGPU PCI reset blocked"):
    fake_nvdev(pci_dev, wpr2=1)._reset_if_wpr2_up()

  pci_dev.read_config.assert_not_called()
  pci_dev.write_config_flush.assert_not_called()
  pci_dev.reset.assert_not_called()


def test_tinygpu_wpr2_reset_can_be_forced(monkeypatch):
  monkeypatch.setenv("TINYGPU_FORCE_RESET", "1")
  pci_dev = object.__new__(APLRemotePCIDevice)
  pci_dev.read_config = Mock(return_value=pci.PCI_COMMAND_MASTER)
  pci_dev.write_config_flush, pci_dev.reset = Mock(), Mock()

  fake_nvdev(pci_dev, wpr2=1)._reset_if_wpr2_up()

  pci_dev.write_config_flush.assert_called_once_with(pci.PCI_COMMAND, 0, 2)
  pci_dev.reset.assert_called_once_with()


def test_native_pci_wpr2_keeps_existing_reset_behavior(monkeypatch):
  monkeypatch.delenv("TINYGPU_FORCE_RESET", raising=False)
  pci_dev = Mock()
  pci_dev.read_config = Mock(return_value=pci.PCI_COMMAND_MASTER)

  fake_nvdev(pci_dev, wpr2=1)._reset_if_wpr2_up()

  pci_dev.write_config_flush.assert_called_once_with(pci.PCI_COMMAND, 0, 2)
  pci_dev.reset.assert_called_once_with()


def test_clean_wpr2_does_not_touch_pci(monkeypatch):
  monkeypatch.delenv("TINYGPU_FORCE_RESET", raising=False)
  pci_dev = object.__new__(APLRemotePCIDevice)
  pci_dev.read_config, pci_dev.write_config_flush, pci_dev.reset = Mock(), Mock(), Mock()

  fake_nvdev(pci_dev, wpr2=0)._reset_if_wpr2_up()

  pci_dev.read_config.assert_not_called()
  pci_dev.write_config_flush.assert_not_called()
  pci_dev.reset.assert_not_called()
