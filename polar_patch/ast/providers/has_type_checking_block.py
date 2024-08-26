import logging
from typing import TYPE_CHECKING

import libcst.matchers as m
from libcst import BaseMetadataProvider
from libcst.metadata import BatchableMetadataProvider

if TYPE_CHECKING:
  import libcst as cst

logger = logging.getLogger(__name__)


class IfTypeCheckingProvider(BatchableMetadataProvider[BaseMetadataProvider[bool]]):
  def __init__(self) -> None:
    logger.info("Finding `if TYPE_CHECKING:` block in file")
    super().__init__()
    self.has_type_checking_block = False

  def visit_If(self, node: "cst.If") -> None:
    if m.matches(node, m.If(test=m.Name("TYPE_CHECKING"))):
      self.has_type_checking_block = True

  def leave_Module(self, original_node: "cst.Module") -> None:
    self.set_metadata(original_node, self.has_type_checking_block)
