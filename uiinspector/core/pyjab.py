from __future__ import annotations
from ctypes import byref
from typing import Any, Dict, Mapping, Optional, Tuple, Generator
from pyjab.jabdriver import JABDriver, JABElement, By
from pyjab.common.types import JOBJECT64
from pyjab.common.exceptions import JABException
import time
import re

class JException(Exception):
    pass

class JElementNotFoundException(JException):
    pass

class JTimeoutError(JException):
    pass

TIMEOUT = 60
IGNORED_EXCEPTIONS = (JElementNotFoundException, JABException)

class JDriver(JABDriver):
    
    @property
    def root_element(self) -> JElement:
        return self._root_element

    def init_jab(self) -> None:
        # load AccessBridge dll file
        self.bridge = self.serv.load_library(self._bridge_dll)
        self.bridge.Windows_run()
        # setup message queue for actor scheduler
        self._run_actor_sched()
        # wait java window by title and get hwnd if not specific hwnd and vmid
        if not (self.hwnd or (self.vmid and self.accessible_context)):
            self.hwnd = self.wait_java_window_by_title(
                title=self.title, timeout=self._timeout
            )
        # get vmid and accessible_context by hwnd
        if self.hwnd:
            self.accessible_context, self.vmid = self._get_accessible_context_from_hwnd(
                self.hwnd
            )
        # get hwnd by vmid and accessible_context
        elif self.vmid and self.accessible_context:
            # must have vmid and accessible_context
            top_level_object = self.bridge.getTopLevelObject(
                self.vmid, self.accessible_context
            )
            self.hwnd = self.bridge.getHWNDFromAccessibleContext(
                self.vmid, top_level_object
            )
        else:
            raise RuntimeError(
                "At least hwnd or vmid and accessible_context is required"
            )
        # check if Java Window HWND valid
        if not self._is_java_window(self.hwnd):
            raise RuntimeError(f"HWND:{self.hwnd} is not Java Window, please check!")
        self.pid = self.get_pid_from_hwnd()
        self._root_element = JElement(
            bridge=self.bridge,
            hwnd=self.hwnd,
            vmid=self.vmid,
            accessible_context=self.accessible_context
        )

    def get_accessible_context_at(self, x: int, y: int) -> JElement:
        """
        Retrive an AccessibleContext object of the window or object that is under the mouse pointer
        """
        acc = JOBJECT64()
        self.bridge.getAccessibleContextAt(self.vmid, self.accessible_context, x, y, byref(acc))
        return JElement(
            bridge=self.bridge,
            hwnd=self.hwnd,
            vmid=self.vmid,
            accessible_context=acc
        )

    def quit(self):
        """
        Kill java process
        """
        self.__exit__(None, None, None)

    def find_element_by_levels(self, search_levels: Tuple[Dict], visible = False) -> JElement:
        return self._root_element.find_element_by_levels(search_levels, visible=visible)

    def find_element_by_search_properties(self, visible = False, **search_properties) -> JElement:
        return self._root_element.find_element(visible=visible, search_properties=search_properties)

class JElement(JABElement):

    def __init__(self,
            bridge = None,
            hwnd = None,
            vmid = None,
            accessible_context = None,
            depth = 0):
        super().__init__(bridge, hwnd, vmid, accessible_context)
        self.depth = depth

    def find_element_by_levels(self, search_levels: Tuple[Dict] | Dict, visible = False, timeout = TIMEOUT) -> JElement:
        """
        Find element according to levels, each level contains search properties.
        search_levels must be a tuple consisting of dict or a dict.
        """
        if isinstance(search_levels, dict):
            search_levels = [search_levels]

        end = time.time() + timeout
        while True:
            try:
                jelement = self
                for search_properties in search_levels:
                    jelement = jelement.find_element_by_search_properties(
                        visible=visible,
                        **search_properties)
                return jelement
            except (JElementNotFoundException, JABException) as ex:
                if (cur:=time.time()) > end:
                    raise ex
                time.sleep(min(0.5, end-cur))
            
    
    def find_element_by_search_properties(self, visible = False, **search_properties) -> JElement:
        """
        Find element according to search properties.
        Available properties: 
        - role
        - name
        - regex_name
        - depth
        - description
        - states
        - found_index
        """
        return self.find_element(visible=visible, search_properties=search_properties)


    def find_element(self, by = None, value = None, visible = False, *, search_properties = None):
        find_properties = {}

        if by and by in [
            By.NAME,
            By.DESCRIPTION,
            By.ROLE,
            By.STATES,
            By.OBJECT_DEPTH,
            By.CHILDREN_COUNT,
            By.INDEX_IN_PARENT
        ]:
            find_properties[by] = value
        if search_properties is not None:
            assert isinstance(search_properties, Mapping), 'Incorrect search properties'
        else:
            search_properties = {}

        find_properties.update(**search_properties)

        if not find_properties:
            raise JException('Must provide at least one element property')

        if 'regex_name' in find_properties:
            find_properties.update(regex_name=re.compile(find_properties['regex_name']))
        
        depth = find_properties.get('depth', 0)
        max_depth = self.depth + depth if depth else 0xffffffff

        index = find_properties.get('found_index', 1)
        found_index = 0
        for descendant in self._generate_all_childs(visible, max_depth):
            # print(descendant.role, descendant.depth, descendant.name)
            if self._compare_func(find_properties, descendant):
                found_index += 1
                if found_index != index:
                    continue
                return descendant

        raise JElementNotFoundException(f'JElement not found for {find_properties}.')

    def _generate_all_childs(self, visible = False, max_depth = 0xffffffff) -> Generator[JElement]:
        if max_depth <= self.depth:
            return

        jelement = self
        # pre:JElement = None
        for child in self._generate_childs_from_element(jelement, visible):
            # if pre:
            #     pre.release_jabelement()
            # pre = child
            yield child
            yield from child._generate_all_childs(visible, max_depth)


    def _generate_childs_from_element(self, jelement: JElement = None, visible: bool = False):
        jelement = self
        if visible:
            children_count = self._get_visible_children_count(
                jelement.accessible_context
            )
            info = self._get_visible_children(jelement.accessible_context)
            for index in range(children_count):
                yield JElement(
                    jelement.bridge,
                    jelement.hwnd,
                    jelement.vmid,
                    info.children[index],
                    jelement.depth + 1
                )
        else:
            for index in range(jelement.children_count):
                child_acc = jelement.bridge.getAccessibleChildFromContext(
                    jelement.vmid, jelement.accessible_context, index
                )
                yield JElement(
                    jelement.bridge, jelement.hwnd, jelement.vmid, child_acc,
                    jelement.depth + 1
                )

    def _compare_func(self, search_properties: Dict, jelement: JElement):
        """
        Compare search properties and JElement properties
        """
        for key, value in search_properties.items():
            if key == 'role' and jelement.role != value:
                return False
            elif key == 'name' and jelement.name != value:
                return False
            elif key == 'regex_name' and not value.match(jelement.name):
                return False
            elif key == 'depth' and jelement.depth - self.depth != value:
                return False
            elif key == 'description' and jelement.description != value:
                return False
            elif key == 'index_in_parent' and jelement.index_in_parent != value:
                return False
            elif key == 'states' and set(jelement.states.split(',')) != set(value.split(',')):
                return False
        return True

    def get_accessible_child_from_context(self, index: int) -> JElement:
        child_ac = self.bridge.getAccessibleChildFromContext(self.vmid, self.accessible_context, index)
        if self.bridge.getObjectDepth(self.vmid, child_ac) != -1:
            return JElement(self.bridge, self.hwnd, self.vmid, child_ac, self.depth + 1)

    def get_accessible_parent_from_context(self) -> JElement:
        parent_ac = self.bridge.getAccessibleParentFromContext(self.vmid, self.accessible_context)
        if self.bridge.getObjectDepth(self.vmid, parent_ac) != -1:
            return JElement(self.bridge, self.hwnd, self.vmid, parent_ac, self.depth - 1)

    def __del__(self):
        self.release_jabelement()

    def request_focus(self) -> bool:
        return self.bridge.requestFocus(self.vmid, self.accessible_context)

    def set_caret_postision(self, position: int) -> bool:
        return self.bridge.setCaretPosition(self.vmid, self.accessible_context, position)

    # keyboard function
    def press_key(self, *keys):
        self.win32_utils._press_key(*keys)

    def press_hold_release_key(self, *keys):
        self.win32_utils._press_hold_release_key(*keys)

    def paste_text(self, text, timeout=TIMEOUT):
        end = time.time() + TIMEOUT
        while True:
            try:
                self.clear(True)
                self.win32_utils._paste_text(text)
                self._wait_for_value_to_be(text, self.text)
                return
            except:
                pass
            if time.time() > end:
                raise JTimeoutError(f'Failed to paste text, text: {text}')

    def simulate_send_text(self, text, timeout=TIMEOUT):
        end = time.time() + TIMEOUT
        while True:
            try:
                self.send_text(text, True)
                return
            except:
                pass
            if time.time() > end:
                raise JTimeoutError(f'Failed to send text, text: {text}')


    def _wait_for_value_to_be(self, expected_value: Optional[str], actual_value, timeout: int = 5,
                              error_msg_function: str = None):
        start = time.time()
        while True:
            if (
                    expected_value
                    and actual_value == expected_value
                    or not expected_value
                    and not actual_value
            ):
                return
            current = time.time()
            elapsed = round(current - start)
            if elapsed >= timeout:
                if error_msg_function:
                    _error_msg = f"Failed to {error_msg_function} in '{timeout}' seconds"
                else:
                    _error_msg = f"Failed to wait for expected value '{expected_value}' in '{timeout}' seconds"
                raise JTimeoutError(_error_msg)
            actual_value = self.text

    @staticmethod
    def exists(ancestor: JElement, search_levels: Tuple[Dict]|Dict, timeout: float) -> bool:
        try:
            ancestor.find_element_by_levels(search_levels, timeout=timeout)
            return True
        except JElementNotFoundException:
            pass
        return False


class JDriverWait:
    def __init__(
        self, jdriver: JDriver, 
        timeout = TIMEOUT, 
        poll_frequency = 1, 
        ignored_exceptions = None):

        self._jdriver = jdriver
        self._timeout = timeout
        self._poll_frequency = poll_frequency
        self.igored_exceptions = ignored_exceptions if ignored_exceptions else IGNORED_EXCEPTIONS

    def until(self, method, message = '') -> Any:
        stacktrace = None
        end = time.time() + self._timeout
        while True:
            try:
                result = method(self._jdriver)
                if result:
                    return result
            except self.igored_exceptions as ex:
                stacktrace = getattr(ex, 'stacktrace', None)
            if time.time() > end:
                break
            time.sleep(self._poll_frequency)

        raise JTimeoutError(message, stacktrace)