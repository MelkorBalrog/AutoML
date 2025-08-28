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

# Version History
- 0.2.177 - Serialize STPA documents for model exports and provide unit test coverage.
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
