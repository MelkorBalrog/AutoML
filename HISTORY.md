<!--
# Author: Miguel Marina <karel.capek.robotics@gmail.com>
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Copyright (C) 2025 Capek System Safety & Robotic Solutions
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
-->

## 0.2.273 - 2025-09-10

- Restore geometry-manager bindings after native reparenting so detached
  widgets resize with their floating windows instead of tracking the original
  notebook container.
- Capture geometry manager configuration for widgets prior to reparenting and
  reapply it once Tk acknowledges the new parent window across native and Tk
  code paths.
- Expand detachment regression coverage with grouped geometry-manager tests to
  guard pack, grid, and place restoration logic alongside Tk notification
  checks.

## 0.2.272 - 2025-09-10

- Synchronise Tkinter's Python widget hierarchy after native reparenting so
  detached diagrams follow the floating window geometry instead of the
  originating notebook.
- Extend regression coverage to ensure Python-level parent references update
  when the Linux reparenting path executes.

## 0.2.271 - 2025-09-10

- Notify Tk after reparenting detached widgets so floating windows resize with
  their own containers instead of following the original notebook geometry.
- Extend reparenting regression coverage to assert Tk notification occurs on
  both Linux and Windows code paths.

## 0.2.270 - 2025-09-10

- Restore standard decorations on detached notebooks so floating windows offer
  minimize, maximize, and close buttons when tabs snap out of the main frame.
- Update dockable diagram floating windows to retain full window controls and
  add regression coverage asserting transient styling is no longer applied.

## 0.2.269 - 2025-09-10

- Replace the floating notebook with a dedicated container frame so dockable
  diagrams float reliably on Windows without Tk ``can't add ... as slave``
  errors and withdraw floating windows after re-docking.
- Extend dockable window tests to cover floating container behavior and window
  withdrawal lifecycle.

## 0.2.268 - 2025-09-10

- Cancel pending ``after`` callbacks on tabs prior to detaching dockable
  diagrams, preventing ``invalid command name`` errors when floating.

## 0.2.267 - 2025-09-10

- Forget tab before floating dockable diagrams to avoid Tk reparent errors.

## 0.2.266 - 2025-09-10

- Supply diagram title when detaching dockable windows to satisfy
  ``DockableDiagramWindow.float``.

## 0.2.265 - 2025-09-04

- Provide ``win`` property for ``DockableDiagramWindow`` so detached tabs
  create a floating window without attribute errors.

## 0.2.264 - 2025-09-04

- Create dedicated tab frames before docking so the document notebook is
  never inserted into itself, preventing Tk "can't add ... as slave" errors.

## 0.2.263 - 2025-09-04

- Skip reparenting when a diagram already resides in the target notebook
  and guard against SetParent failures when widgets and parents match.

## 0.2.262 - 2025-09-04

- Cancel pending callbacks on the parent notebook before reparenting
  docked or floated diagrams so Windows no longer raises ``SetParent
  failed`` errors.

## 0.2.261 - 2025-09-04

- Register target notebook tab before reparenting widgets to catch
  add failures early and strengthen rollback to restore the original
  notebook when registration fails.

## 0.2.260 - 2025-09-04

- Cancel pending Tk ``after`` callbacks before reparenting docked or
  floated diagram frames so OS-level reparenting succeeds on Windows.
- Update `DockableDiagramWindow` to invoke the cancellation prior to
  both dock and float operations.

## 0.2.259 - 2025-09-04

- Reparent widgets before registering tabs and provide dockable window
  helper that adds tabs safely when notebooks are empty.

## 0.2.258 - 2025-09-04

- Register target tab before widget reparenting so notebooks track tabs
  prior to moving their children. Add regression test ensuring registration
  precedes widget transfer.

## 0.2.257 - 2025-09-04

- Restore reparent-first tab transfer after placeholder registration proved
  unreliable, ensuring tabs move with their children across windows.
- Simplify detachment tests to match the reverted logic.

## 0.2.256 - 2025-09-04

- Use placeholder tabs to register targets prior to widget reparenting and
  fall back to reparent-first logic when placeholder registration fails.
- Add regression tests covering both placeholder registration and fallback
  behavior.

## 0.2.255 - 2025-09-04

- Register target tab before reparenting widgets to ensure rollback of
  failed moves and to detect tabs across windows.
- Expand cross-window detachment tests to confirm tab registration precedes
  widget reparenting.

## 0.2.254 - 2025-09-04

- Restore native OS-level reparenting for tab moves so notebooks transfer tabs
  across windows without cloning frames.
- Update cross-window detachment tests to verify original widgets persist when
  moved between notebooks.

## 0.2.253 - 2025-09-04

- Realize new tab container before moving children so widgets transfer correctly
  without reparenting the original tab.

## 0.2.252 - 2025-09-04

- Rebuild tab containers during detachment to avoid OS-level reparenting and
  preserve widget state across windows

## 0.2.251 - 2025-09-04

- Reparent detached tabs across toplevel windows using native OS APIs so
  widgets move without cloning
- Share robust `cancel_after_events` helper to avoid stray callback errors

## 0.2.249 - 2025-09-04

- Move tabs between notebooks without cloning via `WidgetTransferManager`
- Cancel pending `after` callbacks and forget source tab before re-parenting

## 0.2.248 - 2025-09-04

- Restore clone-based tab detachment to avoid Tk reparenting errors
- Prune inanimate duplicates so detached windows keep one toolbox and diagram

# Version History
- 0.2.247 - Fix widget transfer to use keyword arguments when adding tabs,
          preventing detachment errors.
- 0.2.246 - Track expected children by widget identity when hiding unexpected
          widgets during tab detachment so tabs keep their toolbox and diagram
          while only inert duplicates are hidden.
- 0.2.245 - Hide unexpected widgets during tab detachment so only the edge
          toolbox and diagram remain visible. Replace destructive pruning with
          geometry unmapping and expand detached-tab regression tests.
- 0.2.244 - Destroy unexpected widgets during tab detachment so only the
          edge toolbox and diagram persist while stray duplicates are removed.
- 0.2.243 - Guard widget pruning against missing expected children so
          detached windows never drop toolbox and diagram widgets.
- 0.2.242 - Restore duplicate pruning during tab detachment so only the
          edge toolbox and diagram remain visible in detached windows.
- 0.2.241 - Fix widget pruning logic so detached tabs keep the first
          toolbox and last diagram while unmapping any stray duplicates.
- 0.2.240 - Unmap unexpected widgets during tab detachment and drop
          destructive heuristics so detached tabs retain a single toolbox
          and diagram. Add regression tests for detached tab content.
- 0.2.237 - Enforce keyword-only layouts and cancelled parameters in
          ``_clone_widget`` and add regression test confirming detached
          tabs render with and without a layouts mapping.
- 0.2.236 - Route tab detachment through ``DetachedWindow`` so window creation,
          toolbar packing and lifecycle hooks are handled by a dedicated
          utility. Update detachment tests to use the new API.
- 0.2.235 - Introduce ``DetachedWindow`` helper hosting detached diagrams with
          functional toolboxes and event bindings. Add grouped window tests.
- 0.2.234 - Guard ``root.deletecommand`` when the Tcl command table is missing
          or lacks the callback identifier so widget cleanup avoids
          ``invalid command name`` logs. Add regression tests covering
          missing command entries during detachment and destruction.
- 0.2.233 - Cancel after-callbacks before moving tabs and reinitialize
          toolboxes and parent-phase hooks so detached windows keep
          functional toolboxes and avoid "invalid command name" errors.
- 0.2.232 - Guard bug icon antenna drawing from negative coordinates to
             prevent Tk errors. Add regression test.
- 0.2.231 - Populate toolbox groups from connection rules so Entities and Safety &
          Security Mgmt categories expose all rule-defined elements and
          relations. Add grouped tests for toolbox externals.
- 0.2.230 - Preserve toolbox contents after undo, redo and clipboard operations by
          refreshing active frames. Add regression tests for sync and
          refresh routines.
- 0.2.229 - Route risk assessment work products to the Risk Assessment menu group.
          - Preserve governance toolbox contents after diagram edits by
          retaining relation tools across focus changes. Add tests
          confirming focus events do not drop relations.
- 0.2.228 - Preserve toolbox frames for all open governance diagrams by
          avoiding global memory cleanup during toolbox switches.
- 0.2.227 - Remove relation filtering when rebuilding toolboxes so all
          defined relationships remain visible across diagram sessions.
- 0.2.226 - Map all nodes appearing in connection rules to toolbox groups and
          retain unmapped external relations for Safety & AI toolbox.
- 0.2.225 - Scope toolbox caches to diagram sessions and clean obsolete
          frames when windows close. Add regression tests ensuring related
          elements and relationships persist across sequential diagrams.
- 0.2.224 - Deduplicate relations only within each toolbox category so
          Governance Core no longer prunes shared relations. Rebuild
          toolboxes without cross-category seeding and add persistence
          tests for non-core categories.
- 0.2.223 - Reset relation tool lists on window focus change/close and guard
          toolbox rebuilds so relation filtering runs only when diagrams
          supply explicit filters. Add regression test for sequential
          windows.
- 0.2.222 - Scope toolbox caches to individual diagrams and clear them on
          rebuild or window close. Add prefix-based cache eviction helper and
          tests.
- 0.2.221 - Restore Governance Core toolboxes from pristine templates after
          every rebuild so other diagram sessions cannot strip relations or
          related elements.
- 0.2.220 - Rebuild Governance Core toolbox from pristine definitions after
          global filtering and deduplication so all core relations and related
          elements remain visible across diagram sessions.
- 0.2.219 - Guard Governance Core from all relation filtering and dedup
           passes so its related elements and relationships are always
           visible. Add helper tests covering the exemption logic.
- 0.2.218 - Deep-copy toolbox definitions so Governance Core relations remain
           intact across multiple diagram windows. Add regression test.
- 0.2.217 - Maintain Governance Core relations and related elements when
           global relation tools are active and deduplicate others.
- 0.2.216 - Preserve complete Governance Core relationship listings by
           exempting Governance Core from global relation filtering and
           cross-category deduplication. Extract helper functions to reduce
           toolbox rebuild complexity.
- 0.2.215 - Ensure hazard and threat analysis work products activate their
           parent tool groups so lifecycle phase menus like "Qualitative
           Analysis" enable when diagrams (e.g. HAZOP) are present.
- 0.2.214 - Record intermediate drop positions during diagram moves so
           undo steps through each drag instead of jumping to the initial
           placement.
          - Detect common toolbox attributes during toolbar discovery so
            detached windows retain their original toolboxes.
          - Pack identified toolboxes into floating windows and invoke any
            available ``_switch_toolbox`` hooks.
          - Add grouped tests confirming detached architecture and STPA
            windows display functional toolboxes.
          - Parse and rewrite all widget path references in bound command
            strings and option scripts during tab cloning.
          - Reschedule ``after`` callbacks on cloned widgets and expand
            option reference rewriting to menu commands and postcommands.
          - Add grouped tests confirming hover and click callbacks fire in
            detached windows.
          - Cancel Tk ``after`` callbacks whose scripts reference detached widgets.
          - Guard ``root.deletecommand`` when Tcl command table is missing.
          - Add grouped regression tests ensuring animated buttons detach and
            close without ``invalid command name`` logs.
- 0.2.213 - Call `_switch_toolbox` after rebuilding toolboxes so detached
            governance diagrams display the selected toolbox.
          - Add governance toolbox visibility tests for detached tabs.
          - Rewrite bound event command strings during widget cloning so
            bindings reference cloned widgets.
          - Add grouped hover and click tests verifying command rewrites.
          - Clone toolboxes for all window subclasses during tab detachment.
          - Add grouped tests verifying detached architecture, STPA and GSN
            windows retain functional toolboxes.
          - Rewrite bound event command strings during widget cloning so
            bindings reference cloned widgets.
          - Add grouped hover and click tests verifying command rewrites.
          - Replace original toplevel paths in cloned widget ``bindtags`` so
            detached tabs propagate events to their new windows.
          - Add regression tests verifying hover and click events on detached
            tab widgets.
- 0.2.212 - Move core API into dedicated package and expose service
            methods via DLL wrappers.
          - Guard memory manager caches and processes with thread locks and
            add concurrent cleanup tests to ensure active items remain
            protected.
- 0.2.211 - Defer initial toolbox switch so Governance Core related elements
            appear immediately without tab toggling.
- 0.2.210 - Always expose Governance Core toolbox so governance diagrams show
            consistent elements regardless of configuration.
          - Monitor process memory usage, trim freed heap pages and clean
            cached objects when memory exceeds configurable thresholds.
          - Deduplicate Governance Core toolbox relations across categories for
            consistent element display.
- 0.2.209 - Run AutoML core on the main thread and register it with the
            thread manager to prevent Tk asynchronous deletion errors.
- 0.2.208 - Run memory and service managers through central thread manager and
            execute the main application under thread supervision.
- 0.2.207 - Remove threaded service manager and launch core directly.
- 0.2.206 - Internal version synchronisation.
- 0.2.205 - Launch AutoML core through service manager and allow non-daemon
           service threads with join support.
- 0.2.204 - Introduce threaded service manager to lazily load services,
           restart recoverable threads and shut down unused services.
          - Introduce threaded service manager to lazily load services,
          restart recoverable threads and shut down unused services.
- 0.2.203 - Preserve widget creation order across geometry managers so detached
          tabs retain left-side toolboxes.
- 0.2.202 - Guard toolbar frame lookup against destroyed widgets so tab
          detachment skips invalid paths without raising ``TclError``.
- 0.2.201 - Factor tab detachment into `_create_floating_window`,
           `_clone_tab_contents`, and `_post_clone_cleanup` helpers.
           Split `_remove_duplicate_widgets` into traversal and pruning
           utilities to lower cyclomatic complexity.
- 0.2.200 - Group toolbar and callback detachment tests for duplicate removal,
           hover reset, click functionality and after-event cleanup.
- 0.2.199 - Check root Tcl commands before deletion when cancelling callbacks and add regression test for destroying animated tabs.
- 0.2.198 - Copy widget ``bind`` events during cloning and rewrite button
          option references so detached toolbar commands target cloned widgets.
          - Add regression tests verifying detached toolbar button callbacks
            and hover state resets on leave.
- 0.2.197 - Explicitly destroy stray toolbar frames during tab detachment.
          - Add grouped regression test ensuring detached windows contain
            only a single toolbar frame.
- 0.2.196 - Refactor tab detachment helpers to reduce complexity and remove
          duplicate widget pruning logic from `_detach_tab` and
          `_remove_duplicate_widgets`.
          - Gracefully handle missing ``safety_analysis`` when assigning FMEA
            data so unit tests can instantiate ``AutoMLApp`` without full
            initialization.
          - Add grouped toolbar detachment tests covering duplicate removal, hover state reset, and click callbacks.
          - Rebind toolbar button callbacks to cloned widgets during detachment.
          - Add integration test ensuring detached toolbar buttons trigger container methods.
          - Preserve hover bindings when cloning widgets.
          - Replicate `<Enter>`/`<Leave>` events and `bindtags` during widget
            cloning so hover state resets correctly.
          - Add grouped regression tests verifying standard Button hover state
            normalises after detachment.
          - Clone toolbar frames during tab detachment, removing originals and
          rebinding button command and hover events so detached toolbars remain
          functional.
          - Add grouped regression tests ensuring a single toolbar row exists
            after detachment and toolbar buttons still invoke callbacks.
- 0.2.195 - Introduce generic DLL bridge calling Python services.
          - Expose automl_core functions through a dynamic library and add regression tests invoking standard library functions via the bridge.
          - Cancel Tk ``after`` callbacks using direct Tcl calls to avoid
          AttributeError during root destruction and copy widget images with
          preserved dimensions to prevent duplicated button icons when detaching
          tabs.
          - Add regression tests ensuring toolbar images remain singular and
            destroying the root raises no AttributeError after detachment.
- 0.2.194 - Clone widgets using keyword configuration to respect CapsuleButton's
          signature and preserve options like cursor.
          - Add regression test ensuring cursor configuration copies correctly.
- 0.2.193 - Continue cloning siblings when configuration copy fails and log
          offending widgets.
          - Skip missing child clones instead of raising to avoid cascading
            errors.
          - Add grouped tests covering explorer and diagram windows to ensure
            full trees detach without exceptions.
- 0.2.192 - Handle widgets with ``configure`` returning ``None`` during tab
          cloning to avoid errors and copy options safely.
          - Skip configuration iteration when unavailable and fall back to
            ``tk.Widget.configure``.
          - Add regression tests covering CapsuleButton, TranslucidButton and
            canvas-based widgets.
- 0.2.191 - Cancel root-level Tk ``after`` callbacks tied to widget paths and
          - Bootstrap diagnostics manager with numeric interval to avoid
          startup TypeError.
          - Add grouped bootstrap test verifying polling manager initialisation.
          - Validate polling interval type to prevent runtime TypeError.
          - Cancel root-level Tk ``after`` callbacks tied to widget paths and
          track identifiers stored in ``_animate`` attributes.
          - Add grouped regression tests ensuring tab detachment and closure
            leave no "invalid command name" messages.
          - Validate polling interval type to prevent runtime TypeError.
          - Add grouped tests ensuring invalid callable intervals raise errors.
- 0.2.190 - Run crash logger and model loader maintenance in background threads.
          - Add grouped tests covering threaded services.
- 0.2.189 - Cache JSON configuration loads and run memory cleanup in a
          background thread to improve performance.
          - Group config loader tests and add caching regression check.
- 0.2.188 - Re-establish hover image bindings after cloning or detaching buttons
          so highlight effects persist across detached windows.
          - Extend grouped tests validating hover behaviour after detachment.
- 0.2.187 - Apply persistent `bindtags` to diagram canvases so selection and
          movement interactions remain functional after detaching tabs.
          - Add grouped regression tests covering selection and drag on
            detached canvases.
- 0.2.186 - Restore toolbox selector combobox bindings after detaching tabs so
          switching toolboxes updates the visible toolbox.
          - Add regression test confirming toolbox selection in detached
            windows changes the displayed toolbox.
- 0.2.185 - Guard ``cancel_after_events`` against destroyed roots and silence
          errors when closing detached windows.
          - Add grouped regression tests ensuring no "invalid command name" or
            ``AttributeError`` logs after detaching or destroying roots.
- 0.2.184 - Create dedicated ``PhotoImage`` copies when detaching tabs to avoid
          shared Tk handles on reattached widgets.
          - Add regression test verifying toolbar button images keep size after
            detaching and reattaching.
- 0.2.183 - Avoid duplicate canvas images when detaching tabs by copying
          items explicitly instead of using ``tk::canvas copy``.
          - Add grouped regression test ensuring canvas clones contain
            no unexpected image items.
          - Limit after-event cancellation to widget-specific callbacks, preserving
          internal Tk behaviour when detaching tabs.
          - Prevent duplicated controls and "invalid command name" errors after
          detaching tabs.
          - Update tests to cover widget-bound callback cleanup.
- 0.2.182 - Rebind CapsuleButton `<Enter>`/`<Leave>` events when cloning
          detached tabs to preserve hover behaviour.
          - Add grouped tests exercising hover callbacks on detached buttons.
          - Copy canvas tag bindings when detaching tabs so selection events
          like ``<Button-1>`` remain active on cloned diagrams. Added
          regression test ensuring nodes in detached canvases stay
          selectable.
          - Replicate canvas tag bindings when cloning detached tabs so diagram items
          retain double-click handlers.
          - Add tests verifying diagram item double-click callbacks remain
            functional after detachment.
          - Skip canvas item copying for self-drawing canvases to prevent
          duplicate elements when detaching widgets like ``CapsuleButton``.
          - Added regression tests ensuring cloned CapsuleButton widgets render
          a single image and text.
- 0.2.181 - Clone canvas window items recursively so detached tabs preserve
          embedded widget layouts and content.
          - Instantiate canvases using their original subclass to avoid
            option mismatches.
          - Copy canvas items through a dedicated helper that recreates
            ``window`` entries with cloned widgets.
- 0.2.180 - Ensure cloned tabs preserve widget layout and state for all
          - Introduce C-based arithmetic API compiled as DLL and expose
          MathService using the library. Add regression test validating
          DLL-backed addition.
          - Ensure cloned tabs preserve widget layout and state for all
          descendants. Added grouped tests verifying that labels, buttons,
          tree views, canvases, and toolboxes retain identical data after
          detachment.
          - Parse ``after info`` pairs to cancel callbacks referencing widget
          paths and expose a reusable ``cancel_after_events`` helper.
          - Invoke the cleanup for every widget during tab detachment and when
            destroying ``CapsuleButton`` instances.
          - Add grouped regression tests ensuring no ``_animate`` callbacks
            survive after snapping out or closing detached windows.
          - Clone CapsuleButton widgets without Canvas option errors and
          preserve label text and state during detachment.
          - Clone canvases containing window items by manually iterating
          canvas elements, recursively cloning embedded widgets and
          recreating items to avoid ``tk::canvas copy`` errors.
          - Add regression tests verifying canvases with nested frames and
            controls appear identically after detachment.
- 0.2.179 - Refresh diagram mapping before opening safety management diagrams and
          display an error when the diagram is missing. Add double-click tests
          verifying architecture windows open for existing diagrams.
          - Rebuild and activate governance toolboxes when detaching tabs so
          detached governance diagrams display the toolbox selector and remain
          interactive.
          - Invoke ``_switch_toolbox`` on detached governance clones and pack
            the toolbox frame before raising widgets.
          - Add grouped regression tests ensuring toolbox selectors stay
            functional after detachment.
          - Safeguard CapsuleButton canvas operations against detached widget
          errors by checking widget existence and cancelling animation
          callbacks on destruction.  Add regression tests for detached-tab
          hover and destroy interactions.
          - Cancel root-level Tk ``after`` callbacks referencing widget paths and
          invoke cancellation for all widgets before destruction during tab
          detachment.
          - Iterate over ``after info`` results to remove callbacks tied to a
          widget's Tcl name.
          - Call the improved cleanup routine prior to destroying widgets when
          snapping out tabs.
          - Add grouped regression tests ensuring no ``invalid command name``
          errors after detaching animated buttons.
          - Recreate detached governance diagram canvases and transfer items,
          destroying originals to prevent duplicate canvases.
          - Skip reparented canvases during duplicate pruning.
          - Add regression tests ensuring detached governance diagrams expose
            a single populated canvas.
- 0.2.178 - Reparent governance diagram canvases during tab detachment and
          rebuild toolboxes so detached windows display canvases and toolboxes
          correctly.
          - Preserve explorer toolbars when detaching tabs and rebuild actions
          on empty frames.
          - Add regression tests ensuring toolbar buttons remain present and
            functional after detachment.
          - Cancel CapsuleButton ``after`` callbacks before detaching tabs and
          ensure no scheduled callbacks fire after detachment. Add grouped
          tests for after-event cancellation.
          - Raise cloned widgets before originals are destroyed to preserve
          stacking order during detachment.
          - Add regression tests verifying frames, canvases, and toolboxes
            remain visible after detachment.
- 0.2.177 - Pack requirements editor frame so requirement list displays with columns.
          - Serialize STPA documents for model exports and provide unit test coverage.
          - Pack requirements editor frame so requirement list displays with columns.
          - Safeguard splash launcher against missing version metadata when
           executing bundled binaries.
- 0.2.176 - Instantiate FTA sub-app helpers to avoid missing attributes during fault tree queries.
- 0.2.175 - Resolve circular imports by lazily loading fault-tree helpers and
          decoupling safety analysis utilities from GUI modules.
- 0.2.174 - Move FMEA and FTA implementation into ``analysis.utils`` and
          expose thin service wrappers.
- 0.2.173 - Delegate ``SafetyAnalysisService`` computations to
          ``analysis.utils`` for modular safety analysis helpers.
          - Harden canvas window updates against destroyed widgets and
          call them only for surviving clones.
          - Add regression tests detaching canvas tabs with embedded windows
            to ensure no ``TclError`` occurs.
          - Guard CapsuleButton callbacks against ``TclError`` after
          widget destruction and add grouped detachment event tests.
          - Guard duplicate pruning against missing originals and orphaned
          clones.
          - Skip ``winfo_children`` lookups when originals vanish and ignore
            clones whose parents are absent from the mapping.
          - Add grouped detachment tests confirming frames, treeviews,
            canvases and buttons appear only once after detachment.
          - Guard drag target resolution against ``TclError`` or ``KeyError``
          and detach tabs safely when widgets vanish.
          - Update ``_finalize_drag`` to gracefully handle missing targets.
          - Add regression tests simulating release over destroyed widgets that
          raise ``TclError``.
          - Move FMEA and FTA helpers into ``analysis.utils`` and wrap
          - Delegate ``SafetyAnalysisService`` computations to
          ``analysis.utils`` for modular safety analysis helpers.
          - Move FMEA and FTA helpers into ``analysis.utils`` and wrap
          ``safety_analysis_service`` methods.
          - Prevent duplicate Safety Management Explorer instances and prune
          stray explorer widgets during tab detachment.
          - Compute expected child widgets before pruning and destroy unmapped
            frames or treeviews.
          - Check ``_safety_exp_window.winfo_exists`` to avoid multiple
            explorers in the same tab.
          - Add detachment tests ensuring only one explorer treeview and icon
            column exist after opening or detaching the explorer.
          - Reparent canvases during tab detachment or clone and discard
          originals after copying item colors and tags. Skip reparented
          canvases during duplicate pruning and add regression test
          ensuring detached governance diagrams retain a single
          interactive canvas.
          - Rebuild toolboxes and activate parent phase when detaching tabs
          and ensure detached diagram toolboxes pack left before canvases so
          buttons remain visible. Add grouped toolbox detachment tests
          confirming selector visibility and Select tool persistence.
- 0.2.172 - Move ``SafetyAnalysis_FTA_FMEA`` implementation into
          ``safety_analysis_service`` and remove legacy
          ``core.safety_analysis`` module.
- 0.2.171 - Consolidate FMEA helpers into ``safety_analysis_service`` for
          unified safety analysis management and remove ``fmea_service``
          module.
          - Show splash-style background in workspace when no tabs are open.
          - Guard ``nametowidget`` lookups in Treeview hover handlers so
          detached tabs emit no ``KeyError`` or ``TclError`` when moving the
          cursor across tree items.  Add regression test covering detached
          hover behaviour.
          - Cancel root-level ``after`` callbacks referencing widget paths by
          parsing ``after info`` output. Invoke ``_cancel_after_events`` for
          every cloned or destroyed widget during tab detachment and when
          closing floating windows. Add regression test verifying no
          ``invalid command name`` messages after detaching animated buttons.
          - Compute expected child relationships from clone mapping before duplicate
          pruning and avoid `winfo_children` calls on destroyed widgets.
          - Ensure `_clone_widget` registers every descendant in the mapping and
            raise when cloning fails so pruning has complete information.
          - Add grouped layout tests verifying buttons, canvases, toolboxes and
            scrollbars appear exactly once after detachment.
          - Rebuild or fit diagram toolboxes on detached clones, lifting
          toolbox canvases and buttons prior to destroying originals and
          adding regression tests to ensure detached toolboxes remain
          visible and functional.
- 0.2.170 - Show splash-style background in workspace when no tabs are open.
          - Wrap ``winfo_containing`` in ``try/except`` to guard ``KeyError``
          during drag target resolution and detach tabs safely when widgets
          vanish.  Add regression test simulating release over a destroyed
          widget.
          - Record geometry manager and options before cloning widgets and
          restore layouts for every descendant when detaching tabs.
          Refine duplicate pruning to compare parent/child relationships and
          add nested layout tests covering frames, labels, canvases and
          treeviews.
          - Cancel root-scheduled ``after`` callbacks referencing widget paths
          and invoke `_cancel_after_events` when detaching or closing floating
          windows. Add regression tests to ensure animated widgets raise no
          ``TclError`` or ``AttributeError`` after detachment and closure.
          - Raise cloned widgets before originals are destroyed to avoid
          `TclError` and preserve visibility when detaching tabs.
          - Accept original and clone roots in `_raise_widgets` and traverse a
            cached child list while the original still exists.
          - Invoke `_raise_widgets` ahead of duplicate pruning in `_detach_tab`.
          - Add regression tests ensuring detachment raises no errors and all
            widgets remain visible.
- 0.2.169 - Prune only widgets that duplicate original parent/child relationships,
          ensure all cloned descendants register in the mapping and add layout
          tests verifying frame, label, canvas and treeview retention after
          detachment.
          - Traverse clone mappings when lifting widgets and raise clones
          before pruning duplicates to preserve visibility of overlapping
          widgets after detachment.
- 0.2.168 - Accumulate children from all geometry managers so every widget
          in a tab transfers to the detached window.
- 0.2.167 - Clone children managed by grid/place so all tab contents appear in
          detached windows.
- 0.2.166 - Define root list when pruning clones so tab detachment no longer
          raises `NameError` in `_remove_duplicate_widgets`.
- 0.2.165 - Accept optional clone mappings in `_raise_widgets` to prevent
          `TypeError` during tab detachment and ensure all widgets lift to
          the top of their stacks.
- 0.2.164 - Guard duplicate-pruning against destroyed widgets and retain
          all tab contents when detaching to floating windows.
          - Recursively raise cloned widgets in original stacking order.
          - Add regression tests to verify detached labels, canvases and buttons
            remain visible when overlapping.
          - Guard target notebook lookup when widgets are destroyed during drag.
          - Add regression tests for tab drag detachment including releases over void and destroyed widgets.
          - Refine duplicate widget pruning and enforce clone mapping.
          - Prune only widgets that duplicate mapping relationships during
            detachment.
          - Ensure cloned widgets register in the mapping and log failures.
          - Add layout regression tests verifying frame, label, treeview and
            canvas visibility after detachment.
          - Guard target notebook lookup when widgets are destroyed during drag.
          - Wrap ``winfo_containing`` in ``try/except`` and return ``None`` on failure.
          - Add regression test verifying drag over destroyed widget raises no errors.
          - Cancel pending callbacks for all descendant widgets when detaching or
          closing tabs and guard Tcl command deletions.
          - Add regression tests for animated CapsuleButton detachment to
          prevent invalid command name and ``AttributeError`` exceptions.
          - Preserve geometry options for all descendants when detaching tabs and raise cloned widgets before originals are destroyed to keep z-order.
          - Verify detached labels, entries, canvases and more remain visible.
          - Guard drag target resolution failures and default to tab detachment.
          - Skip Tk ``after`` cancellation when widgets lack roots and
          search identifiers referencing widget names to remove pending
          callbacks.  Add detachment event tests to ensure closing and
          destroying tabs leaves no residual callbacks or ``TclError``.
          - Split widget reference reassignment into helper methods and add unit
          tests for configuration rewiring and canvas window updates.
          - Cancel widget-specific Tk ``after`` callbacks during tab detachment
          to prevent "invalid command name" errors when interacting with
          floating-window widgets.
          - Log failed widget clones and ensure every cloned control fills and
          raises in detached windows.
          - Cancel after callbacks referencing destroyed widgets during tab
          detachment and verify no invalid command messages remain.
          - Guard capsule button events after detachment.
          - Cancel after callbacks on duplicate widgets prior to destruction.
          - Verify detached capsule buttons handle hover and motion safely.
          - Always parent detached windows to the main root so repeated
          detachment yields windows owned by the primary application.
          - Parent detached windows to the main root so tab content remains
          visible and callbacks operate on valid widgets.
          - Raise detached tab widgets so all elements remain visible in floating windows.
          - Parent detached windows to the main root so tab content remains
          visible and callbacks operate on valid widgets.
          - Raise detached tab widgets so all elements remain visible in floating windows.
          - Generate high-definition executable icon and add scalable builder with
          adjustable resolution.
- 0.2.160 - Map Windows system colour names via GetSysColor to avoid invalid
          command errors from temporary Tk roots when darkening capsule buttons.
- 0.2.159 - Coerce capsule button width and height to integers so string
          dimensions clone correctly during tab detachment.
- 0.2.158 - Resolve system colour parsing when darkening capsule buttons to
          prevent detachment crashes on Windows.
- 0.2.157 - Fix explorer detachment to retain window references.
          - Reassign container attributes to cloned children after tab detachment
          - Transfer treeview item images and open flags when cloning tabs so
          icons display and expanded folders remain open after detachment.
          - Preserve explorer data sources when detaching tabs and verify
          governance diagrams remain visible after tab detachment.
- 0.2.156 - Rewire canvas window widgets when cloning tabs so embedded lists,
          diagrams, comboboxes and toolboxes appear in detached windows.
- 0.2.155 - Cancel lingering Tk ``after`` callbacks to avoid animation errors
          when detaching tabs and skip toolbox fitting for destroyed widgets.
- 0.2.154 - Ignore destroyed widgets when measuring toolbox button width.
          - Add grouped detachment regression tests for layouts, canvas cloning,
          scrollbars and GSN diagram tabs.
- 0.2.153 - Reparent tabs via Tk ``winfo`` before cloning to simplify detachment.
          - Clone canvas items, scroll regions and bindings when detaching tabs.
          - Guard tab widget reference rewrites when cloned widgets report no configuration.
          - Preserve mixed geometry layouts when detaching tabs.
- 0.2.152 - Limit fill adjustments to detached tab container so child layouts remain intact.
          - Rewire cloned widgets during tab detachment and remove duplicate controls.
- 0.2.153 - Rebind cloned scrollbars to detached widgets and recompute scrollregions
          so floating toolboxes scroll and resize correctly.
- 0.2.151 - Always clone widgets when detaching tabs to avoid Tk reparent errors.
- 0.2.150 - Strip geometry manager before/after references when cloning widgets
            and mirror grid parent weights so detached tabs retain layout.
- 0.2.149 - Close floating project windows when loading or creating projects.
- 0.2.148 - Reparent detached tab widgets when possible and clone with full
            geometry metadata replication to preserve layout.
- 0.2.147 - Drop parent references when cloning packed widgets so detached tabs
            keep layouts confined to their floating windows.
- 0.2.146 - Debounce explorer hover events and serialize animations to prevent
            runaway expansion and ensure predictable auto-hide behavior.
- 0.2.145 - Cancel Tk after callbacks referencing detached widgets and store
            animation identifiers for reliable tab closure.
- 0.2.144 - Resolve _StyledButton detachment by inspecting base-class signatures and
            falling back to widget text options when cloning tabs.
- 0.2.143 - Cancel widget animations when detaching tabs and default missing text when cloning capsule buttons.
- 0.2.142 - Ensure detached tabs fill newly opened windows and resize with them.
- 0.2.141 - Let detached tabs resize with their windows so cloned widgets expand to fit.
- 0.2.140 - Apply original geometry when cloning tabs so detached windows retain full content layout.
- 0.2.139 - Preserve widget state when detaching tabs so floating windows
            contain full content.
- 0.2.138 - Reduce tab-detachment cyclomatic complexity and ignore master when cloning widgets.
- 0.2.137 - Capture attribute-based widget arguments when cloning tabs and clean up failed detachment windows.
- 0.2.136 - Copy required widget options when cloning tabs so custom controls detach without errors.
- 0.2.135 - Move tab widgets instead of cloning to prevent empty detached windows and ensure only one floating window per drag.
- 0.2.134 - Clone tab contents into brand-new windows so dragged tabs stay
            detached without relying on platform reparenting.
- 0.2.133 - Keep detached tabs in new windows even when reparenting fails by
            packing the tab content into the floating window instead of
            snapping back.
- 0.2.132 - Reparent tabs using geometry-manager fallback to keep detached windows on platforms lacking reparent commands.
- 0.2.131 - Fix splash launcher circular import and add package entry point for Python execution.
- 0.2.130 - Ensure detached windows display tab content and restore tabs when detachment fails.
- 0.2.129 - Remove snap-back fallback when detaching tabs so floating windows persist.
- 0.2.128 - Expose requirement pattern regeneration through config utils for legacy callers.
- 0.2.127 - Use native Tk reparenting when detaching tabs to keep windows alive.
- 0.2.126 - Preserve detached tabs by retaining references to floating windows.
- 0.2.125 - Guard configuration import against external `config` modules in frozen executables.
- 0.2.124 - Import global requirements into core and add lazy service registry with context-managed cleanup.
- 0.2.123 - Define local service registry alias for backwards compatibility.
- 0.2.122 - Expose service registry constants and integrate all services into core.
- 0.2.121 - Lazily load services to avoid circular imports and expose user configuration service.
- 0.2.120 - Integrate all services into central registry and unify core imports.
- 0.2.119 - Replace module imports with service classes and add service orchestration tests.
- 0.2.118 - Wrap structure tree operations in service and delegate from core.
- 0.2.117 - Wrap safety UI helpers in service and delegate from core.
- 0.2.116 - Centralize window helpers into WindowControllersService and refactor core initialization.
- 0.2.115 - Group core managers into ManagersFacadeService, provide compatibility launcher module, and update core initialization.
- 0.2.114 - Wrap versioning review helpers in service and update core initialization.
- 0.2.113 - Wrap reporting helpers in service and delegate PDF/HTML generation.
- 0.2.112 - Wrap validation consistency helpers in dedicated service and refactor core initialization.
- 0.2.111 - Wrap data access queries in service and update core.
- 0.2.110 - Add radial green highlight to gear on splash screen.
- 0.2.109 - Move version history to dedicated HISTORY.md file.
- 0.2.108 - Import UndoRedoService during service setup to fix NameError when launching the application.
- 0.2.107 - Allow importing top-level modules when rewriting legacy mainappsrc paths.
- 0.2.106 - Move clipboard, project properties and undo managers into managers package.
- 0.2.105 - Fix missing mechanism library references in analysis utilities and prevent thread monitor shutdown error.
- 0.2.104 - Render orange AutoML splash title at 1.5x subtitle size.
- 0.2.103 - Render white AutoML splash title using subtitle font at quadruple size.
- 0.2.102 - Fix splash font name retrieval to avoid startup error.
- 0.2.101 - Ensure AutoML splash title font matches subtitle and store ratio for testing.
- 0.2.100 - Use subtitle font for AutoML splash title and size it at double the subtitle.
- 0.2.99 - Double AutoML splash title size for improved visibility.
- 0.2.98 - Render large orange AutoML title with black border.
- 0.2.97 - Enlarge AutoML title and apply per-letter white-to-orange gradient.
- 0.2.96 - Enlarge AutoML title with white-to-orange gradient.
- 0.2.95 - Fix random band generation bug in splash screen.
- 0.2.94 - Add beveled blue splash background and render AutoML title in black.
- 0.2.93 - Replace splash background with properties window color, remove top gradient, and switch title font.
- 0.2.92 - Thicken white horizon, add violet-blue sky gradient, and whiten title text.
- 0.2.91 - Emit light green glow from white horizon into void.
- 0.2.90 - Add light green and white gradient shading to the void.
- 0.2.89 - Render splash screen as a black void with a white horizon.
- 0.2.88 - Add translucent night sky gradient to splash screen.
- 0.2.87 - Use absolute imports for config constants to support bundled executables.
- 0.2.86 - Explicitly include tools package in PyInstaller builds to prevent runtime import errors.
- 0.2.85 - Ensure PyInstaller bundles the tools package by collecting all modules.
- 0.2.84 - Bundle tools package in executable to fix missing module at runtime.
- 0.2.83 - Fix PyInstaller data path for core module and update documentation.
- 0.2.82 - Preserve governance folder structure when saving and loading projects.
- 0.2.81 - Show GSN diagrams as inputs when governance conditions are met and provide compatibility wrapper for ``page_diagram``.
- 0.2.80 - Enforce active-phase governance relations for safety case inputs.
- 0.2.79 - Ensure tools package is available for bundled executable by injecting project root into ``sys.path``.
- 0.2.78 - Open Requirements Matrix in workspace tab and enforce fixed-size dialogs.
- 0.2.77 - Coerce PDF export path to string to support Windows paths.
- 0.2.76 - Delegate basic events access through reporting helpers for PDF report generation.
- 0.2.75 - Delegate root node access through reporting helpers for traceability PDF generation.
- 0.2.74 - Delegate node traversal helper through reporting export for traceability PDF elements.
- 0.2.73 - Delegate top events access through reporting helpers for PDF exports.
- 0.2.72 - Delegate cause-effect data builder to fix PDF report generation.
- 0.2.71 - Expand PDF report generator with template-driven content and enforce `.pdf` extension.
- 0.2.70 - Ensure PDF exports always use the user-selected `.pdf` extension.
- 0.2.68 - Prevent tool tab duplication when switching lifecycle phases.
- 0.2.67 - Activate risk assessment tools only when risk assessment work products exist.
- 0.2.66 - Recognize copied work products in active phase governance diagrams.
- 0.2.70 - Enforce PDF extension on export so files use the selected format.
- 0.2.65 - Always paste to the focused governance diagram and show focused tab details in the status bar.
- 0.2.64 - Fix paste so governance diagrams honor the currently focused tab.
- 0.2.63 - Ensure governance diagram clipboard uses focused tab for copy, cut and paste.
- 0.2.62 - Move PMHF calculation to FTA menu, move PAL calculation to PAA menu and remove Process menu.
- 0.2.61 - Fix parent-node resolution and enable FTA/CTA node creation when PAA mode is active.
- 0.2.60 - Allow adding FTA and CTA nodes regardless of active work product mode.
- 0.2.59 - Reactivate lifecycle phase when focusing governance diagrams to allow editing after opening other analyses.
- 0.2.58 - Fix empty Safety tab when editing nodes in FTA, CTA and PAA diagrams.
- 0.2.57 - Map Task toolbox selection to Action elements so governance diagrams support adding tasks.
- 0.2.56 - Synchronize README version header with source.
- 0.2.55 - Delegate ODD library management to dedicated manager and remove legacy scenario code.
- 0.2.54 - Initialize undo manager during service setup to prevent project load errors.
- 0.2.52 - Move product goal UIs into RequirementsManager and add wrapper methods.
- 0.2.51 - Extract clone-chain resolution into reusable utility.
- 0.2.50 - Extract shared product goal updates into ProductGoalManager.
- 0.2.49 - Move ``from __future__`` annotations imports to top-level of modules.
- 0.2.48 - Provide wrapper for 90° connections and serialize SysML diagrams for export.
- 0.2.47 - Delegate basic event probability updates to probability service to avoid missing risk module method.
- 0.2.46 - Delegate basic event retrieval to FTASubApp to fix invocation mismatch.
- 0.2.45 - Guard AutoML import in package initialisation to avoid circular reference on startup.
- 0.2.44 - Import StyleSetupMixin to prevent startup NameError in AutoMLApp.
- 0.2.43 - Remove duplicate service initialisation and centralise drawing manager.
- 0.2.42 - Integrate initialization mixins to provide setup_services and icons.
- 0.2.41 - Guard RoundedButton creation to prevent duplicate element errors.
- 0.2.40 - Import Syncing_And_IDs during core initialization to prevent startup NameError.
- 0.2.39 - Import SafetyAnalysis_FTA_FMEA during core initialization to prevent startup NameError.
- 0.2.38 - Import ProjectEditorSubApp, RiskAssessmentSubApp and ReliabilitySubApp to prevent startup NameError.
- 0.2.107 - Introduced ConfigService to centralise configuration helpers.
- 0.2.38 - Extract node cloning into dedicated service and delegate from core.
- 0.2.37 - Import TreeSubApp in core to prevent startup NameError.
- 0.2.36 - Delegate add/get/show/link/refresh/collect routines to safety analysis facade.
- 0.2.35 - Wrap update routines within safety analysis facade.
- 0.2.34 - Centralise safety analysis helpers into facade and delegate from core.
- 0.2.87 - Render star field on splash screen for cosmic backdrop.
- 0.2.33 - Extract dialog classes into dedicated modules and update mixins.
- 0.2.32 - Refactor core initialization into mixins for style, services, and icons.
- 0.2.31 - Provide requirements editor export placeholder to prevent export error.
- 0.2.59 - Introduced TrashEater module for proactive resource cleanup.
- 0.2.30 - Instantiate reporting export helper during application start-up.
- 0.2.29 - Instantiate validation consistency helper during application start-up.
- 0.2.28 - Avoid circular import by using application helper in probability calculations.
- 0.2.27 - Import Probability_Reliability in fallback path to avoid initialization error.
- 0.2.103 - Introduced NavigationInputService to unify navigation and window helpers.
- 0.2.26 - Import Syncing_And_IDs in fallback path to avoid initialization error.
- 0.2.25 - Extract page and PAA helpers into dedicated module and delegate from core.
- 0.2.24 - Move UI lifecycle helpers to dedicated class and delegate calls.
- 0.2.23 - Correct default style path so governance diagrams and icons retain their colours.
- 0.2.22 - Re-export add_treeview_scrollbars via gui.utils for legacy compatibility.
- 0.2.25 - Extracted window opening helpers into dedicated class.
- 0.2.21 - Expose DIALOG_BG_COLOR via gui.utils and re-export drawing helper for compatibility.
- 0.2.20 - Re-export logger through gui package to fix DIALOG_BG_COLOR import failure.
- 0.2.19 - Provide compatibility wrapper for splash screen import.
- 0.2.18 - Organized GUI modules into functional subpackages and reduced threat window refresh complexity.
- 0.2.17 - Ensure AutoMLHelper fallback if AutoML module lacks helper export.
- 0.2.16 - Import PurpleButton lazily in custom messagebox to avoid early circular imports.
- 0.2.15 - Lazily import messagebox module to resolve circular import.
- 0.2.14 - Fade out splash screen symmetrically before launching application.
- 0.2.13 - Delegate tab motion events to lifecycle UI to prevent missing handler error.
- 0.2.18 - Organised mainappsrc into core, managers and subapps packages.
- 0.2.12 - Fix property initialisation error in safety analysis facade.
- 0.2.11 - Keep splash screen visible through startup and five-second post-load delay.
- 0.2.10 - Hold splash screen for five seconds after initialisation completes.
- 0.2.9 - Display splash screen during dependency checks and startup.
- 0.2.8 - Renamed core module to `automl_core.py` and launcher to `automl.py`.
- 0.2.7 - Launcher now shows the splash screen during application load.
- 0.2.6 - Introduced WindowControllers class for centralized window management.
- 0.2.5 - Added PDF report generation placeholder and fixed missing menu action.
- 0.2.4 - Centralized diff capture and review tools into ReviewManager.
- 0.2.3 - Moved capsule button into dedicated controls module.
- 0.2.2 - Moved risk assessment helpers into dedicated sub-app.
- 0.2.1 - Extracted review diff and version functions into ReviewManager.
- 0.1.13 - Enhanced after-callback cleanup for detachable tabs and added tests for animated button detachment.
- 0.1.12 - Delegated reliability and risk-analysis windows to dedicated sub-app wrappers.
- 0.1.11 - Split fault-tree and risk assessment logic into dedicated sub-app wrappers.
- 0.1.10 - Centralised constants and moved requirement logic into a RequirementsManager sub-app.
- 0.1.9 - Split diagram creation into dedicated sub-apps and centralised PNG export.
- 0.1.8 - Moved analysis tree logic into a dedicated TreeSubApp wrapper.
- 0.1.7 - Refactored main application into modular sub-apps and added CLI version option.
- 0.1.6 - Fixed version display in Help → About and splash screen.
- 0.1.5 - Added a pastel style with peach actions and steel-blue nodes.
- 0.1.4 - Initial diagram style support documented.
- 0.1.3 - Added context menu actions to remove parts from a diagram or from the model.
- 0.1.2 - Clarified systems safety focus in description and About dialog.
- 0.1.1 - Updated description and About dialog.
- 0.1.0 - Added Help menu and version tracking.
