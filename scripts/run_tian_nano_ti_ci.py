#!/usr/bin/env python3
"""Exact Tian +2 append, explicit source modes and fresh six-wheel offline suites.

Only the named experimental push skips the unchanged general jobs. Every source
and platform suite has a frozen sorted-ID fingerprint, not a test-count minimum.
Checkout-only ingestion/projection helpers are not installed product interfaces.
Platform/external-fixture skips have exact IDs/reasons and are not counted as passes.
--test reproduces the full core inventory; --targeted-core runs only the frozen
complete-module selection, never claiming that excluded core tests passed.
"""
import argparse
import ast
from collections import Counter
from copy import deepcopy
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import venv

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from run_kapoor_phosphate_ci import (
    BRANCH_REF as PREVIOUS_BRANCH_REF, BUILD_COMMAND,
    FULL_JOB_IF as PREVIOUS_FULL_JOB_IF, TARGETED_JOB as PREVIOUS_TARGETED_JOB,
    PREVIOUS_JOBS as EARLIER_JOBS, changed_paths, source_skip_contract,
    validate_targeted_run_scalars, validate_wheel_command,
)
from run_evidence_batch_ci import (
    ExactResult, PACKAGES, clean_env, install_offline_guard, installed_origins,
    require, run, sha256, test_ids, verify_wheels,
)

BASE_COMMIT = '5a9a85c573f590d206cddb4cb7c085f334a0fbc0'
DATA_BASE_COMMIT = '5a9a85c573f590d206cddb4cb7c085f334a0fbc0'
CANDIDATE_COMMIT = '497dcc8495c32b16f02cdedce8b99f6b7d05f2c4'
BRANCH_REF = 'refs/heads/experimental/tian2023-composite-runtime'
FULL_JOB_IF = PREVIOUS_FULL_JOB_IF.replace("') }}\n", "' && github.ref != '" + BRANCH_REF + "') }}\n")
# Keep the existing 90-minute ceiling; do not enlarge it to hide a failure.
# This is a selected core profile followed by complete installed groups.
# Prior hosted jobs completed within this inherited ceiling. That historical
# result does not establish Tian timing or completeness; actual local and
# hosted validation must be reported separately.
HOSTED_TIMEOUT_MINUTES = 90
# This status freezes the technical validation contract only. Parent review
# before publication is still pending; this runner grants no push approval.
FINALIZATION_STATUS = 'reviewed-frozen'
TARGETED_JOB = (PREVIOUS_TARGETED_JOB
                .replace('  kapoor-phosphate-targeted:\n', '  tian-nano-ti-targeted:\n')
                .replace(PREVIOUS_BRANCH_REF, BRANCH_REF)
                .replace('run_kapoor_phosphate_ci.py', 'run_tian_nano_ti_ci.py'))
PREVIOUS_JOBS = EARLIER_JOBS + ('kapoor-phosphate-targeted',)
# Exact implementation and final validation-receipt path inventory.
APPROVED_FILES = frozenset({'.github/workflows/ci.yml',
           'README.md',
           'THIRD_PARTY_NOTICES.md',
           'experimental/material-batches/tian-nano-ti-composites-20261024/INTEGRATION.md',
           'experimental/material-batches/tian-nano-ti-composites-20261024/INTEGRATION_VALIDATION.md',
           'experimental/material-batches/tian-nano-ti-composites-20261024/README.md',
           'experimental/material-batches/tian-nano-ti-composites-20261024/VALIDATION.md',
           'experimental/material-batches/tian-nano-ti-composites-20261024/build_identity_review.py',
           'experimental/material-batches/tian-nano-ti-composites-20261024/identity-review.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/integration-report.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/integration-validation-results.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/integration.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/packet-spec.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/preparation-receipt.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/prepared-packet.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/source-review.json',
           'experimental/material-batches/tian-nano-ti-composites-20261024/validation-results.json',
           'experimental/platform/ci/required_test_ids.json',
           'experimental/platform/ingestion/FORMAL_OVERLAP_AUDIT.md',
           'experimental/platform/ingestion/FORMAL_REVIEW_GAPS.md',
           'experimental/platform/ingestion/INCREMENTAL.md',
           'experimental/platform/ingestion/README.md',
           'experimental/platform/ingestion/nomad_review_boundary.py',
           'experimental/platform/ingestion/test_formal_overlap_audit.py',
           'experimental/platform/ingestion/test_formal_review_gaps.py',
           'experimental/platform/ingestion/test_incremental_independent.py',
           'experimental/platform/ingestion/test_nomad_evidence_compare.py',
           'experimental/platform/ingestion/test_nomad_incremental.py',
           'experimental/platform/ingestion/test_review_boundary.py',
           'experimental/platform/query-service/README.md',
           'experimental/platform/query-service/catalog-tests/test_baseline_compatibility.py',
           'experimental/platform/query-service/catalog-tests/test_bruns_borosilicate.py',
           'experimental/platform/query-service/catalog-tests/test_catalog_baseline.py',
           'experimental/platform/query-service/catalog-tests/test_combined_admission_boundary.py',
           'experimental/platform/query-service/catalog-tests/test_computed_recovery.py',
           'experimental/platform/query-service/catalog-tests/test_computed_v2_second_tranche.py',
           'experimental/platform/query-service/catalog-tests/test_computed_v2_tranche.py',
           'experimental/platform/query-service/catalog-tests/test_family_adjacency.py',
           'experimental/platform/query-service/catalog-tests/test_family_relationships.py',
           'experimental/platform/query-service/catalog-tests/test_formal_project_catalog.py',
           'experimental/platform/query-service/catalog-tests/test_kapoor_phosphate.py',
           'experimental/platform/query-service/catalog-tests/test_local_catalog.py',
           'experimental/platform/query-service/catalog-tests/test_tarasov_pna_bpf.py',
           'experimental/platform/query-service/catalog-tests/test_tian_nano_ti.py',
           'experimental/platform/query-service/materials_query/computed_registry.py',
           'experimental/platform/query-service/materials_query/pins/legacy_baseline.json',
           'experimental/platform/relationships/HBN_PROJECTION.md',
           'experimental/platform/relationships/test_hbn_relationship_projection.py',
           'formal-catalog/README.md',
           'formal-catalog/materials_project_catalog/catalog.py',
           'formal-catalog/tests/test_formal_project_core.py',
           'materials_boundaries/data/materials.json',
           'materials_boundaries/data/reference_properties.json',
           'materials_boundaries/data/sources.json',
           'scripts/run_bruns_borosilicate_ci.py',
           'scripts/run_kapoor_phosphate_ci.py',
           'scripts/run_tarasov_pna_bpf_ci.py',
           'scripts/run_tian_nano_ti_ci.py',
           'tests/fixtures/tian_legacy_document_code_20261024.json',
           'tests/fixtures/tian_legacy_document_recovery_20261024.json',
           'tests/fixtures/tian_nano_ti_data_20261024.json',
           'tests/fixtures/tian_nano_ti_files_20261024.json',
           'tests/legacy_document_recovery.py',
           'tests/material_append_successors.py',
           'tests/test_kapoor_phosphate_ci.py',
           'tests/test_legacy_document_recovery.py',
           'tests/test_tian_nano_ti_ci.py',
           'tests/test_tian_nano_ti_packet.py',
           'tests/test_tian_nano_ti_preservation.py'})

# Complete suite inventories: directory, exact count, SHA-256 of sorted IDs
# encoded as UTF-8 with one trailing newline per ID. No discovered test may
# disappear, be renamed, or be substituted; every skip needs its exact policy.
TEST_GROUPS = {'core': ('tests', 1887, '19a735217c29533c1137a6cfd95b2b58cf88e8cf649848e41012c510434446f7'),
 'query': ('experimental/platform/query-service/catalog-tests',
           233,
           '90f16e8b5ba77595cea0960b733e4cdfab09022a016ee63edc85b09fcbfcd040'),
 'formal': ('formal-catalog/tests', 13, 'a7b9440ac024ff1d520b1850bac6c062491eb406371ab80bac64bc7e701cf9bd'),
 'ingestion': ('experimental/platform/ingestion',
               202,
               'e1734d9028e6bc6412bf2835d3ba410dccc17be67b5175d0750aa9fa9eb1e93c'),
 'relationships': ('experimental/platform/relationships',
                   14,
                   'ee52759a66ac42805869f8bce7a1dc2c6d7b9507f381c158e84ee854c6bcc936'),
 'provider': ('experimental/platform/federation/tests',
              19,
              '60c12178318c669c29320d1ed385a6a05347c5a397f7f3628bd0be4d9bafe669'),
 'transport': ('experimental/platform/query-service/tests',
               37,
               '6ea89371eae5ef5b84607b6890c305d92e85d7a632fd74572a5f9e0746629c4f'),
 'lifecycle': ('experimental/platform/lifecycle/tests',
               25,
               '8017cf5a6cc1324a6eb3fbbd24c66499a66a4f5e035892ae7c1cc1459d77ecee'),
 'integration': ('experimental/platform/tests',
                 18,
                 'fdff229979a751083a10a2c9cb781692d8793d21b6187f230f732d0ac37dc43d')}
# Hosted core coverage is deliberately narrower than --test. These are COMPLETE
# modules, not cherry-picked methods. Keep every discovered case, including new
# runner tests, and separately freeze the exact IDs and their sorted fingerprint.
TARGETED_CORE_MODULES = ('test_bruns_borosilicate_ci',
 'test_bruns_borosilicate_packet',
 'test_bruns_borosilicate_preservation',
 'test_composite_preservation',
 'test_evidence_dedup_preservation',
 'test_family_adjacency_ci',
 'test_family_adjacency_history',
 'test_legacy_document_recovery',
 'test_material_append_merge',
 'test_material_batch_preservation',
 'test_material_bulk_preservation',
 'test_material_catalog_preservation',
 'test_material_class_counts_preservation',
 'test_release_metadata',
 'test_formulation_packet_preparation',
 'test_formulation_packet_integration',
 'test_tarasov_pna_bpf_packet',
 'test_tarasov_pna_bpf_preservation',
 'test_tarasov_pna_bpf_ci',
 'test_kapoor_phosphate_packet',
 'test_kapoor_phosphate_preservation',
 'test_kapoor_phosphate_ci',
 'test_tian_nano_ti_packet',
 'test_tian_nano_ti_preservation',
 'test_tian_nano_ti_ci')
TARGETED_CORE_IDS = ('test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_ci_requires_exact_push_branch_sha_and_clean_checkout',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_complete_inventories_preserve_every_predecessor_and_new_test',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths',
 'test_bruns_borosilicate_ci.BrunsBorosilicateCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_installed_suites_cannot_use_source_skip_exceptions',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_known_skips_never_increment_passed_count',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_missing_execution_or_pass_and_failure_cannot_hide_behind_skips',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_missing_unexpected_duplicate_reason_and_os_drift_fail',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_platform_and_opt_in_counts_are_exact',
 'test_bruns_borosilicate_ci.BrunsBorosilicateSkipPolicyTests.test_windows_privilege_exception_is_one_exact_case_and_reason',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_cli_rejects_conflicting_modes_and_misplaced_dependencies',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_cli_selects_targeted_full_and_installed_modes_unambiguously',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_failed_targeted_execution_cannot_emit_complete',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_full_mode_still_discovers_all_core_tests',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_full_runner_keeps_exact_source_skip_policy',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_hosted_job_uses_targeted_core_and_keeps_installed_protocol',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_real_targeted_discovery_matches_frozen_ids_without_running_cases',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_discovery_loads_complete_modules_not_individual_ids',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_inventory_is_all_cases_from_exact_complete_modules',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_inventory_rejects_missing_duplicate_substituted_and_extra_ids',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_loading_errors_are_not_a_partial_pass',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_results_cannot_use_any_source_skip_exception',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_results_reject_unexecuted_duplicate_failed_or_unpassed_cases',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_runner_emits_honest_coverage_and_never_requests_source_skips',
 'test_bruns_borosilicate_ci.BrunsBorosilicateTargetedCoreTests.test_targeted_summary_distinguishes_excluded_cases_from_passes_and_skips',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_bad_pin_owner_unit_and_statistic_refuse_atomic_output',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_compiler_and_integrator_replay_are_deterministic_immutable_and_detached',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_count_method_unknowns_and_four_percent_cooling_exception',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_forged_packet_and_source_scoped_collision_cannot_upgrade',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_frozen_packet_matches_four_source_recipes_and_density_cells',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_isolated_integration_preserves_every_predecessor_record_and_byte',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_pending_identity_source_and_rights_cannot_integrate',
 'test_bruns_borosilicate_packet.BrunsBorosilicatePacketTests.test_source_attribution_hash_and_candidate_receipt_remain_bound',
 'test_bruns_borosilicate_preservation.BrunsBorosilicatePreservationTests.test_exact_append_and_predecessor_bytes_keep_all_existing_materials',
 'test_bruns_borosilicate_preservation.BrunsBorosilicatePreservationTests.test_file_ledger_restores_exact_readme_and_workflow_and_rejects_drift',
 'test_bruns_borosilicate_preservation.BrunsBorosilicatePreservationTests.test_finite_registry_preserves_every_preexisting_descriptor_and_boundary',
 'test_bruns_borosilicate_preservation.BrunsBorosilicatePreservationTests.test_original_candidate_and_source_assets_remain_unchanged',
 'test_bruns_borosilicate_preservation.BrunsBorosilicatePreservationTests.test_partial_reordered_owner_unit_and_rights_drift_fail_closed',
 'test_composite_preservation.CompositePreservationTests.test_disposable_mixed_catalog_count_refresh_reverses_without_touching_checkout',
 'test_composite_preservation.CompositePreservationTests.test_every_forward_reverse_round_trip_and_changed_successor_fails',
 'test_composite_preservation.CompositePreservationTests.test_every_old_fixture_example_and_provenance_helper_remains_byte_exact',
 'test_composite_preservation.CompositePreservationTests.test_every_old_noncatalog_file_has_exact_accepted_bytes_or_exact_reversal',
 'test_composite_preservation.CompositePreservationTests.test_every_prior_complete_object_locale_value_and_metadata_field_is_exact',
 'test_composite_preservation.CompositePreservationTests.test_evidence_appends_keep_exact_original_objects_order_and_other_metadata',
 'test_composite_preservation.CompositePreservationTests.test_exact_edit_parser_rejects_bad_offsets_shapes_types_and_overlap',
 'test_composite_preservation.CompositePreservationTests.test_independent_appended_records_and_labels_pass_but_old_object_mutations_fail',
 'test_composite_preservation.CompositePreservationTests.test_independent_ledger_adapter_pins_and_exact_public_anchor',
 'test_composite_preservation.CompositePreservationTests.test_legacy_chain_is_exact_and_unreviewed_bytes_fail_closed',
 'test_composite_preservation.CompositePreservationTests.test_malformed_foreign_duplicate_and_forged_ledger_entries_fail',
 'test_composite_preservation.CompositePreservationTests.test_only_exact_compatibility_transformations_and_no_removed_test_declarations',
 'test_composite_preservation.CompositePreservationTests.test_readme_normalization_rejects_false_counts_changed_prose_and_outside_edits',
 'test_evidence_dedup_preservation.EvidenceDedupPreservationTests.test_existing_355_and_402_file_pins_remain_exact',
 'test_evidence_dedup_preservation.EvidenceDedupPreservationTests.test_helper_ledger_and_five_exact_predecessors_are_pinned',
 'test_evidence_dedup_preservation.EvidenceDedupPreservationTests.test_ledger_drift_and_duplicate_keys_are_rejected_without_mutation',
 'test_evidence_dedup_preservation.EvidenceDedupPreservationTests.test_unreviewed_successors_inputs_and_edit_mutations_fail_closed',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_ci_requires_exact_event_branch_sha_and_clean_checkout',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_inventories_are_nonempty_unique_and_preserve_affected_modules',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_scope_rejects_catalog_data_unlisted_paths_and_nonfiles',
 'test_family_adjacency_ci.FamilyAdjacencyCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
 'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_all_material_workflow_views_keep_their_exact_file_pins',
 'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_code_only_workflow_round_trip_retains_old_rejection',
 'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_data_registry_and_every_material_ledger_remain_unchanged',
 'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_only_one_workflow_has_a_pinned_code_successor',
 'test_family_adjacency_history.FamilyAdjacencyHistoryTests.test_unknown_boundaries_and_ledger_or_edit_drift_are_rejected',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_closed_manifest_binding_hash_and_no_adjustment_contract',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_cross_batch_source_designation_collision_is_atomic',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_linked_grade_designation_and_alias_cannot_create_another_identity',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_missing_crosswalk_is_reportable_but_not_integrable',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_rehashed_tampering_cannot_replace_full_packet_replay',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_single_packet_replays_then_integrates_idempotently',
 'test_formulation_packet_integration.FormulationPacketIntegrationTests.test_v1_still_accepts_its_original_four_descriptors_and_encoding',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_context_collisions_and_wrong_row_ownership_fail_atomically',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_frozen_four_formulation_replay_preserves_all_facts_and_zero_increment',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_crosswalk_review_and_license_remain_pending_without_upgrade',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_missing_properties_wrong_units_and_untraceable_provenance_are_rejected',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_output_path_and_existing_artifact_refusals_preserve_input_bytes',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_prepared_packet_validation_recompiles_input_instead_of_trusting_report',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_reidentified_designation_or_alias_cannot_evade_existing_identity',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_repeated_write_and_cli_keep_identical_bytes_and_mtime',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_shared_contexts_and_explicit_grade_multiple_states_do_not_multiply_identity',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_source_and_baseline_pins_reject_changed_inputs_before_writing',
 'test_formulation_packet_preparation.FormulationPacketPreparationTests.test_strict_json_rejects_duplicate_nonfinite_and_overflow_values',
 'test_kapoor_phosphate_ci.KapoorCandidateAndFreezeTests.test_candidate_artifacts_are_exact_and_not_promoted_to_completed_claims',
 'test_kapoor_phosphate_ci.KapoorCandidateAndFreezeTests.test_candidate_manifest_rejects_wrong_history_status_and_packet',
 'test_kapoor_phosphate_ci.KapoorCandidateAndFreezeTests.test_installed_failure_cannot_emit_terminal_completion',
 'test_kapoor_phosphate_ci.KapoorCandidateAndFreezeTests.test_pending_profile_and_budget_cannot_authorize_scope',
 'test_kapoor_phosphate_ci.KapoorCandidateAndFreezeTests.test_skip_contract_is_reused_without_a_new_exception',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_ci_requires_exact_push_branch_sha_and_clean_checkout',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_complete_inventories_preserve_every_predecessor_and_new_test',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths',
 'test_kapoor_phosphate_ci.KapoorPhosphateCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_cli_rejects_conflicting_modes_and_misplaced_dependencies',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_cli_selects_targeted_full_and_installed_modes_unambiguously',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_failed_targeted_execution_cannot_emit_complete',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_full_mode_still_discovers_all_core_tests',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_full_runner_keeps_exact_source_skip_policy',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_hosted_job_uses_targeted_core_and_keeps_installed_protocol',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_real_targeted_discovery_matches_frozen_ids_without_running_cases',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_discovery_loads_complete_modules_not_individual_ids',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_inventory_is_all_cases_from_exact_complete_modules',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_inventory_rejects_missing_duplicate_substituted_and_extra_ids',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_loading_errors_are_not_a_partial_pass',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_results_cannot_use_any_source_skip_exception',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_results_reject_unexecuted_duplicate_failed_or_unpassed_cases',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_runner_emits_honest_coverage_and_never_requests_source_skips',
 'test_kapoor_phosphate_ci.KapoorPhosphateTargetedCoreTests.test_targeted_summary_distinguishes_excluded_cases_from_passes_and_skips',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_baseline_hash_drift_is_refused',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_baseline_pins_and_runtime_catalog_bytes_remain_unchanged',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_duplicate_source_alias_and_designation_do_not_create_materials',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_forged_prepared_values_or_report_cannot_replace_exact_replay',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_icp_oes_compositions_are_exact_analyzed_mol_percent',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_measurement_evidence_does_not_claim_scientific_validation',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_missing_property_cannot_write_partial_candidate',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_one_state_and_property_per_identity_do_not_admit_materials',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_p60_contextual_collision_stays_source_qualified_and_separate',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_pending_source_identity_or_rights_never_become_handoff_ready',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_repeated_measurements_do_not_become_independent_sample_count',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_replay_and_idempotent_write_preserve_bytes_and_mtime',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_room_temperature_and_prepared_state_do_not_supply_unknown_conditions',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_six_labels_and_density_cells_preserve_reported_precision',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_source_attribution_and_original_document_hash_are_bound',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_source_wide_sd_ceiling_is_not_a_row_uncertainty_or_mean',
 'test_kapoor_phosphate_packet.KapoorPhosphatePacketTests.test_wrong_density_unit_is_rejected',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_candidate_adapter_preserves_methods_source_oracles_and_assertions',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_candidate_artifacts_and_computed_reviews_remain_unchanged',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_exact_append_preserves_every_predecessor_byte_and_identity',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_file_ledger_restores_exact_predecessor_files_and_rejects_drift',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_partial_reordered_duplicate_and_fact_drift_fail_closed',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_registry_preserves_all_predecessor_descriptors_and_chronology',
 'test_kapoor_phosphate_preservation.KapoorPhosphatePreservationTests.test_six_finite_descriptors_preserve_one_packet_and_runtime_id_order',
 'test_legacy_document_recovery.LegacyDocumentRecoveryTests.test_exact_call_site_reversal_changes_no_old_assertion_or_normalizer',
 'test_legacy_document_recovery.LegacyDocumentRecoveryTests.test_exact_document_chains_reach_unchanged_original_release_pins',
 'test_legacy_document_recovery.LegacyDocumentRecoveryTests.test_helper_ledgers_and_call_site_inventory_are_byte_pinned',
 'test_legacy_document_recovery.LegacyDocumentRecoveryTests.test_modified_prose_and_attribution_still_fail_original_release_checks',
 'test_legacy_document_recovery.LegacyDocumentRecoveryTests.test_reordered_chains_and_forged_fixtures_fail_closed',
 'test_material_append_merge.MaterialAppendMergeTests.test_conflicting_existing_id_fails_without_partial_mutation',
 'test_material_append_merge.MaterialAppendMergeTests.test_merge_idempotent_preserves_inputs_and_baseline_order',
 'test_material_append_merge.MaterialAppendMergeTests.test_reordering_new_append_tables_produces_identical_merge',
 'test_material_append_merge.MaterialAppendMergeTests.test_unvalidated_append_cannot_gain_coverage',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_all_355_predecessor_files_round_trip_exactly',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_corrupt_incomplete_duplicate_or_foreign_ledgers_fail',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_every_exact_update_rejects_arbitrary_bytes_and_wrong_edits',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_every_prior_catalog_object_and_metadata_is_preserved',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_existing_catalog_only_claim_evidence_append_contract_is_retained',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_fixed_objects_cannot_be_mutated_removed_or_duplicated',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_future_material_appends_require_truthful_live_readme_counts',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_independent_catalog_appends_recover_pinned_release_without_mutating_inputs',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_ledger_helper_admission_and_accepted_tree_are_pinned',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_production_modules_have_no_test_preservation_imports',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_readme_rejects_untrue_counts_changed_prose_and_missing_markers',
 'test_material_batch_preservation.MaterialBatchPreservationTests.test_seven_new_material_admissions_are_exact_independent_subsets',
 'test_material_bulk_preservation.ExactOutputMigrationTests.test_each_migration_has_exact_reversible_nonempty_byte_edits',
 'test_material_bulk_preservation.ExactOutputMigrationTests.test_output_ledger_is_finite_and_anchored_to_untouched_v034_snapshot',
 'test_material_bulk_preservation.ExactOutputMigrationTests.test_source_fidelity_bridge_drops_no_unlisted_field',
 'test_material_bulk_preservation.FreshGraphResolutionTests.test_no_cached_success_after_any_graph_component_is_mutated',
 'test_material_bulk_preservation.FreshGraphResolutionTests.test_one_validation_per_operation_and_fresh_validation_on_repeat',
 'test_material_bulk_preservation.FreshGraphResolutionTests.test_results_are_detached_and_ordered_and_do_not_mutate_inputs',
 'test_material_bulk_preservation.InstalledWheelAppendGuardTests.test_each_missing_historical_id_duplicate_or_relabel_is_rejected',
 'test_material_bulk_preservation.InstalledWheelAppendGuardTests.test_exact_historical_cohorts_survive_unrelated_mixed_appends',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_accepted_tree_ledger_helper_and_admission_are_pinned',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_all_402_predecessor_files_round_trip_exactly',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_bridge_restores_only_the_pinned_finite_taxonomy_and_labels',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_every_retained_object_metadata_and_label_is_checked_before_projection',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_exact_edits_reject_changed_successor_before_image_and_offsets',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_independent_suffix_appends_do_not_mutate_or_hide_retained_data',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_malformed_incomplete_duplicate_and_foreign_ledgers_are_rejected',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_new_admissions_pin_complete_objects_without_a_live_registry_ceiling',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_no_production_module_imports_test_preservation',
 'test_material_bulk_preservation.MaterialBulkPreservationTests.test_readme_counts_and_noncount_prose_remain_checked',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_all_old_noncatalog_files_recover_exact_accepted_bytes',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_baseline_sources_and_initial_admitted_records_are_exact_subsets',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_corrupt_or_incomplete_ledgers_fail',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_current_material_summary_is_derived_from_actual_registry',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_new_ledger_helper_and_admission_are_pinned',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_readme_normalization_rejects_changed_prose_and_untrue_counts',
 'test_material_catalog_preservation.MaterialCatalogPreservationTests.test_successors_round_trip_and_arbitrary_bytes_fail',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_all_old_ledgers_remain_unchanged_and_new_ledger_mutations_fail',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_changed_bytes_paths_types_and_before_images_cannot_use_the_bridge',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_five_exact_predecessors_round_trip_including_ci_and_helpers',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_helper_ledger_and_three_snapshot_resources_are_pinned',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_readme_exact_recovery_and_all_seven_original_material_chains',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_snapshot_is_fixed_while_marked_totals_follow_an_append_rehearsal',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_snapshot_sentence_matches_actual_core_classes_and_only_natural_reaches_goal',
 'test_material_class_counts_preservation.MaterialClassCountsPreservationTests.test_wrong_class_counts_dates_duplicate_sentences_and_prose_fail_closed',
 'test_release_metadata.ReleaseMetadataTests.test_all_current_engine_labels_match_package',
 'test_release_metadata.ReleaseMetadataTests.test_build_configuration_and_readme_use_current_version',
 'test_release_metadata.ReleaseMetadataTests.test_comparison_embedded_snapshots_and_exact_references',
 'test_release_metadata.ReleaseMetadataTests.test_local_schema_reference_targets_exist',
 'test_release_metadata.ReleaseMetadataTests.test_version_is_one_build_readable_literal',
 'test_tarasov_pna_bpf_ci.TarasovCandidateAndFreezeTests.test_candidate_artifacts_are_exact_and_not_promoted_to_completed_claims',
 'test_tarasov_pna_bpf_ci.TarasovCandidateAndFreezeTests.test_candidate_manifest_rejects_wrong_history_status_and_packet',
 'test_tarasov_pna_bpf_ci.TarasovCandidateAndFreezeTests.test_installed_failure_cannot_emit_terminal_completion',
 'test_tarasov_pna_bpf_ci.TarasovCandidateAndFreezeTests.test_pending_profile_and_budget_cannot_authorize_scope',
 'test_tarasov_pna_bpf_ci.TarasovCandidateAndFreezeTests.test_skip_contract_is_reused_without_a_new_exception',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_ci_requires_exact_push_branch_sha_and_clean_checkout',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_complete_inventories_preserve_every_predecessor_and_new_test',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_cli_rejects_conflicting_modes_and_misplaced_dependencies',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_cli_selects_targeted_full_and_installed_modes_unambiguously',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_failed_targeted_execution_cannot_emit_complete',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_full_mode_still_discovers_all_core_tests',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_full_runner_keeps_exact_source_skip_policy',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_hosted_job_uses_targeted_core_and_keeps_installed_protocol',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_real_targeted_discovery_matches_frozen_ids_without_running_cases',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_discovery_loads_complete_modules_not_individual_ids',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_inventory_is_all_cases_from_exact_complete_modules',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_inventory_rejects_missing_duplicate_substituted_and_extra_ids',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_loading_errors_are_not_a_partial_pass',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_results_cannot_use_any_source_skip_exception',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_results_reject_unexecuted_duplicate_failed_or_unpassed_cases',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_runner_emits_honest_coverage_and_never_requests_source_skips',
 'test_tarasov_pna_bpf_ci.TarasovPNABPFTargetedCoreTests.test_targeted_summary_distinguishes_excluded_cases_from_passes_and_skips',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_additional_state_does_not_increase_identity_count',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_cured_state_and_tensile_method_do_not_supply_missing_statistics',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_duplicate_alias_or_designation_cannot_manufacture_an_identity',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_exact_five_source_rows_and_decimal_precision',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_forged_values_counts_or_readiness_do_not_replace_replay',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_invalid_pin_owner_missing_property_unit_and_scientific_upgrade_fail_atomically',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_isolated_report_preserves_all_baseline_bytes_and_does_not_admit',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_nominal_formulations_preserve_all_three_source_conflicts_and_exclusions',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_pending_identity_transcription_and_rights_cannot_integrate',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_receipt_and_candidate_commit_bind_actual_packet_bytes',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_replay_is_deterministic_immutable_and_outside_runtime',
 'test_tarasov_pna_bpf_packet.TarasovPnaBpfPacketTests.test_source_attribution_document_hash_and_finite_identity_review',
 'test_tarasov_pna_bpf_preservation.TarasovPnaBpfPreservationTests.test_candidate_artifacts_and_computed_reviews_remain_unchanged',
 'test_tarasov_pna_bpf_preservation.TarasovPnaBpfPreservationTests.test_exact_append_preserves_every_predecessor_byte_and_identity',
 'test_tarasov_pna_bpf_preservation.TarasovPnaBpfPreservationTests.test_file_ledger_restores_exact_predecessor_files_and_rejects_drift',
 'test_tarasov_pna_bpf_preservation.TarasovPnaBpfPreservationTests.test_partial_reordered_duplicate_and_fact_drift_fail_closed',
 'test_tarasov_pna_bpf_preservation.TarasovPnaBpfPreservationTests.test_registry_preserves_all_predecessor_descriptors_and_chronology',
 'test_tian_nano_ti_ci.TianCandidateAndFreezeTests.test_candidate_artifacts_are_exact_and_not_promoted_to_completed_claims',
 'test_tian_nano_ti_ci.TianCandidateAndFreezeTests.test_candidate_manifest_rejects_wrong_history_status_and_packet',
 'test_tian_nano_ti_ci.TianCandidateAndFreezeTests.test_installed_failure_cannot_emit_terminal_completion',
 'test_tian_nano_ti_ci.TianCandidateAndFreezeTests.test_pending_profile_and_budget_cannot_authorize_scope',
 'test_tian_nano_ti_ci.TianCandidateAndFreezeTests.test_skip_contract_is_reused_without_a_new_exception',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_ambiguous_yaml_scalars_and_index_package_builds_fail',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_append_rejects_count_preserving_rewrite_partial_order_metadata_and_id_drift',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_ci_requires_exact_push_branch_sha_and_clean_checkout',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_complete_inventories_preserve_every_predecessor_and_new_test',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_current_payload_pins_exact_packet_data_baseline_and_unchanged_reviews',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_installed_protocol_is_six_wheels_no_index_and_all_complete_suites',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_missing_duplicate_substituted_or_extra_inventory_ids_are_rejected',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_previous_jobs_keep_every_step_and_only_new_branch_is_gated',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_scope_rejects_unlisted_deleted_nonfile_and_symlink_paths',
 'test_tian_nano_ti_ci.TianNanoTiCITests.test_unknown_predecessor_workflow_shapes_are_rejected',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_cli_rejects_conflicting_modes_and_misplaced_dependencies',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_cli_selects_targeted_full_and_installed_modes_unambiguously',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_failed_targeted_execution_cannot_emit_complete',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_full_mode_still_discovers_all_core_tests',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_full_runner_keeps_exact_source_skip_policy',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_hosted_job_uses_targeted_core_and_keeps_installed_protocol',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_real_targeted_discovery_matches_frozen_ids_without_running_cases',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_discovery_loads_complete_modules_not_individual_ids',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_inventory_is_all_cases_from_exact_complete_modules',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_inventory_rejects_missing_duplicate_substituted_and_extra_ids',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_loading_errors_are_not_a_partial_pass',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_results_cannot_use_any_source_skip_exception',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_results_reject_unexecuted_duplicate_failed_or_unpassed_cases',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_runner_emits_honest_coverage_and_never_requests_source_skips',
 'test_tian_nano_ti_ci.TianNanoTiTargetedCoreTests.test_targeted_summary_distinguishes_excluded_cases_from_passes_and_skips',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_actual_density_cells_and_literal_source_labels',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_archive_manifest_corroboration_does_not_claim_primary_pdf_bytes',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_baseline_or_source_record_hash_drift_is_refused',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_baseline_pins_and_actual_catalog_counts_are_unchanged',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_comparator_exclusion_and_finite_identity_inputs',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_density_statistics_basis_and_porosity_remain_unknown',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_density_unknowns_do_not_inherit_tensile_temperature_or_count',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_duplicate_alias_or_designation_does_not_create_an_identity',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_forged_values_or_admission_cannot_replace_exact_replay',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_measurement_and_review_are_not_scientific_approval',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_missing_percent_symbol_is_preserved_with_method_qualification',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_missing_property_cannot_write_partial_candidate',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_nominal_loadings_are_source_qualified_and_not_final_composition',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_pending_source_identity_or_license_blocks_handoff',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_replay_and_idempotent_write_preserve_bytes_and_mtime',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_source_license_attribution_and_selected_document_are_bound',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_two_composite_identities_have_one_extruded_state_and_property_each',
 'test_tian_nano_ti_packet.TianNanoTiPacketTests.test_wrong_density_unit_is_rejected',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_candidate_adapter_preserves_methods_source_oracles_and_assertions',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_candidate_artifacts_and_computed_reviews_remain_unchanged',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_exact_append_preserves_every_predecessor_byte_and_identity',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_file_ledger_restores_exact_predecessor_files_and_rejects_drift',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_partial_reordered_duplicate_and_fact_drift_fail_closed',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_registry_preserves_all_predecessor_descriptors_and_chronology',
 'test_tian_nano_ti_preservation.TianNanoTiPreservationTests.test_single_descriptor_preserves_exact_packet_and_runtime_order')
TARGETED_CORE_COUNT = 305
TARGETED_CORE_SHA256 = '9d3b0fb714ff5d8fea75e8d69d4a61fb6df0de701fcc1ffe2af47fc305e88ea1'

PACKET_PATH = 'experimental/material-batches/tian-nano-ti-composites-20261024/prepared-packet.json'
PACKET_SHA256 = 'eec719edfb9803551df5337c31430faf916169c0bd2e4bac1b8f72d2f79e69ab'
BASELINE_HASHES = {'materials': 'ec6a73ea89a267a55eb77d8b189f27deee75b5aaabf24941a9b4da5e2ac85c33',
 'reference_properties': '29c826fc9a1bd67d0012384ee956740ab91fd2a87be7ab33aa7cc548c1be3e1f',
 'sources': 'a02ac67aadae86e118065e97cae95013b6d7edd85516e3fcf66396deefdd58c2'}
RESOURCE_HASHES = {'materials.json': '8ad95e381232906bce1c0e2df777ed7856f2ad27e25200913fc3ad50482e5293',
 'reference_properties.json': '32327221035bd9cc439a2107b4c857629f69276ace7d54df21ce3013720d7c8a',
 'sources.json': '360d0fc46605805173773ae30a01efcd5ba08cc262b140460a6b39c3b9434bd1'}
QUERY_BASELINE_SHA256 = '8aa3073504462d2e892c12565a30db1d4df189f21ffaeba57fdbe7bb7ed83093'
GRAPH_COUNTS = {'identity': 1161, 'grade': 31, 'state': 1162, 'property': 1173, 'source': 127}
DELTA_COUNTS = {'identity': 2, 'grade': 0, 'state': 2, 'property': 2, 'source': 1}
PRIMARY_COUNTS = {'metal': 32, 'inorganic': 59, 'polymer': 30, 'composite': 30, 'natural': 1010}
FORMAL_COUNTS = {'formal_project_admission_count': 1185,
 'legacy_source_qualified_identity_count': 1161,
 'reviewed_computed_composition_count': 24,
 'categories': {'metal': 44, 'inorganic': 71, 'polymer': 30, 'composite': 30, 'natural': 1010}}
PRESERVED_RESOURCES = (
    'experimental/platform/query-service/materials_query/pins/family_relationships.json',
    'formal-catalog/materials_project_catalog/data/formal_computed_review.json',
    'materials_boundaries/data/observations.json',
    'materials_boundaries/data/computational_predictions.json',
    'experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json',
    'experimental/platform/examples/reviewed-computed-seed/scoped-review-input.json',
)


CANDIDATE_ARTIFACTS = ('experimental/material-batches/tian-nano-ti-composites-20261024/README.md',
 'experimental/material-batches/tian-nano-ti-composites-20261024/VALIDATION.md',
 'experimental/material-batches/tian-nano-ti-composites-20261024/build_identity_review.py',
 'experimental/material-batches/tian-nano-ti-composites-20261024/identity-review.json',
 'experimental/material-batches/tian-nano-ti-composites-20261024/packet-spec.json',
 'experimental/material-batches/tian-nano-ti-composites-20261024/preparation-receipt.json',
 'experimental/material-batches/tian-nano-ti-composites-20261024/prepared-packet.json',
 'experimental/material-batches/tian-nano-ti-composites-20261024/source-review.json',
 'experimental/material-batches/tian-nano-ti-composites-20261024/validation-results.json',
 'tests/test_tian_nano_ti_packet.py')


def require_frozen():
    require(FINALIZATION_STATUS == 'reviewed-frozen', 'Tian profile is pending parent freeze')
    require(type(HOSTED_TIMEOUT_MINUTES) is int and HOSTED_TIMEOUT_MINUTES > 0,
            'Hosted validation budget is pending')
    require(APPROVED_FILES and len(QUERY_BASELINE_SHA256) == 64,
            'Reviewed scope or product-manifest hash is pending')
    require(len(TEST_GROUPS) == 9 and all(count > 0 and len(digest) == 64
            for _, count, digest in TEST_GROUPS.values()), 'Complete inventories are pending')
    require(TARGETED_CORE_COUNT == len(TARGETED_CORE_IDS) > 0
            and len(TARGETED_CORE_SHA256) == 64, 'Targeted complete-module inventory is pending')
    require('    timeout-minutes: ' + str(HOSTED_TIMEOUT_MINUTES) + '\n' in TARGETED_JOB,
            'Workflow budget differs from the frozen inherited ceiling')


def validate_candidate_artifacts():
    for name in CANDIDATE_ARTIFACTS:
        path = ROOT / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(ROOT.resolve()),
                'Candidate artifact is not a regular repository file: ' + name)
        raw = path.read_bytes()
        if name == 'tests/test_tian_nano_ti_packet.py':
            # Only the frozen test adapter may differ from the reviewed candidate.
            # Its exact byte reversal is checked before the immutable comparison.
            tests = ROOT / 'tests'
            if str(tests) not in sys.path:
                sys.path.insert(0, str(tests))
            import material_append_successors as successors
            import material_append_history as history
            require(Path(successors.__file__).resolve() == (tests / 'material_append_successors.py').resolve()
                    and Path(history.__file__).resolve() == (tests / 'material_append_history.py').resolve(),
                    'Candidate test recovery requires checkout-only frozen helpers')
            ledger = successors.file_ledger('tian-nano-ti-composites-20261024')
            require(name in ledger['updates'], 'Missing exact candidate-test recovery entry')
            raw = history.recover_file(raw, ledger['updates'][name])
        require(raw == git('show', CANDIDATE_COMMIT + ':' + name),
                'Frozen candidate artifact changed: ' + name)


def validate_manifest(manifest):
    require(manifest['released_main_count'] == 1081, 'Released main count changed')
    require(manifest['baseline_sha256'] == BASELINE_HASHES and manifest['status_adjustments'] == [],
            'Candidate manifest predecessor or status boundary changed')
    require(manifest['batches'] == [{'id': 'tian-nano-ti-composites-20261024',
            'candidate_commit': CANDIDATE_COMMIT,
            'packet': {'path': 'prepared-packet.json', 'sha256': PACKET_SHA256}}],
            'Candidate manifest does not name the exact reviewed packet')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=30)


def expected_workflow(baseline):
    """Every preexisting job is byte-identical except complementary guards."""
    validate_targeted_run_scalars(TARGETED_JOB)
    commands = [line.removeprefix('      - run: ') for line in TARGETED_JOB.splitlines()
                if line.startswith('      - run: python -m pip wheel ')]
    require(commands == [BUILD_COMMAND], 'Expected the exact six-project wheel build')
    validate_wheel_command(commands[0])
    require(baseline.count(PREVIOUS_FULL_JOB_IF) == 2, 'Unexpected frozen full-job guards')
    for name in PREVIOUS_JOBS:
        require(baseline.count('  ' + name + ':\n') == 1, 'Missing previous experiment job: ' + name)
    require('  tian-nano-ti-targeted:\n' not in baseline, 'Predecessor already contains this job')
    for name in ('unit-and-schema', 'windows-composite'):
        marker = '  ' + name + ':\n' + PREVIOUS_FULL_JOB_IF
        require(baseline.count(marker) == 1, 'Unexpected predecessor job block: ' + name)
        baseline = baseline.replace(marker, '  ' + name + ':\n' + FULL_JOB_IF, 1)
    return baseline + TARGETED_JOB


def validate_names(names, *, root=ROOT):
    require(all(type(name) is str for name in names), 'Changed paths must be strings')
    require(APPROVED_FILES, 'Approved file inventory is not frozen')
    unexpected = sorted(set(names) - APPROVED_FILES)
    require(not unexpected, 'Changes exceed Tian integration scope: ' + ', '.join(unexpected))
    for name in names:
        path = root / name
        require(not path.is_symlink() and path.is_file() and path.resolve().is_relative_to(root.resolve()),
                'Approved path must remain a regular repository file: ' + name)


def validate_event(head):
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        require(os.environ.get('GITHUB_EVENT_NAME') == 'push', 'Scoped CI requires a push event')
        require(os.environ.get('GITHUB_REF') == BRANCH_REF, 'Scoped CI requires its exact experiment branch')
        require(os.environ.get('GITHUB_SHA') == head, 'Checkout differs from the pushed GITHUB_SHA')
        require(not git('status', '--porcelain', '--untracked-files=normal'), 'Scoped CI checkout must be clean')


def validate_scope():
    require_frozen()
    head = git('rev-parse', 'HEAD').decode().strip()
    subprocess.run(['git', 'merge-base', '--is-ancestor', BASE_COMMIT, head], cwd=ROOT, check=True, timeout=30)
    validate_event(head)
    names = set(changed_paths(git('diff', '--name-status', '--no-renames', '-z', BASE_COMMIT, 'HEAD', '--')))
    names.update(changed_paths(git('diff', '--name-status', '--no-renames', '-z', 'HEAD', '--')))
    names.update(name for name in git('ls-files', '--others', '--exclude-standard', '-z').decode().split('\0') if name)
    validate_names(names)
    prior = git('show', BASE_COMMIT + ':.github/workflows/ci.yml').decode('utf-8')
    require((ROOT / '.github/workflows/ci.yml').read_bytes().decode('utf-8') == expected_workflow(prior),
            'Workflow differs from the exact predecessor plus Tian integration job')
    payload = installation_payload()
    result = {'base_commit': BASE_COMMIT, 'head': head, 'branch_ref': BRANCH_REF,
              'changed_files': sorted(names), 'old_job_steps_preserved': True,
              'previous_experiment_jobs_preserved': True, 'exact_targeted_job_preserved': True,
              'packet_sha256': PACKET_SHA256, 'delta_counts': DELTA_COUNTS,
              'graph_counts': GRAPH_COUNTS, 'formal_counts': FORMAL_COUNTS,
              'query_baseline': payload['query_baseline'], 'resource_hashes': payload['resource_hashes']}
    print(json.dumps(result, indent=2), flush=True)
    return result


def inventory_fingerprint(ids):
    return sha256(''.join(identifier + '\n' for identifier in sorted(ids)).encode('utf-8')).hexdigest()


def validate_inventory(name, ids):
    if name == 'targeted-core':
        count, digest = TARGETED_CORE_COUNT, TARGETED_CORE_SHA256
        require(tuple(sorted(ids)) == TARGETED_CORE_IDS, 'Targeted core exact IDs differ')
    else:
        _, count, digest = TEST_GROUPS[name]
    require(count > 0 and len(digest) == 64, 'Exact inventory is not frozen: ' + name)
    require(len(ids) == len(set(ids)) == count and inventory_fingerprint(ids) == digest,
            'Exact inventory differs from the fixed sorted-ID fingerprint: ' + name)


def declared_test_ids(relative, *, predecessor=False):
    """Independent declared-ID oracle used by regression tests, not discovery."""
    names = (git('ls-tree', '-r', '--name-only', BASE_COMMIT, '--', relative).decode().splitlines()
             if predecessor else [path.relative_to(ROOT).as_posix() for path in (ROOT / relative).glob('test*.py')])
    result = []
    for name in sorted(names):
        path = Path(name)
        if path.parent.as_posix() != relative or not path.name.startswith('test') or path.suffix != '.py':
            continue
        raw = git('show', BASE_COMMIT + ':' + name) if predecessor else (ROOT / name).read_bytes()
        for node in ast.parse(raw).body:
            if isinstance(node, ast.ClassDef):
                result.extend(path.stem + '.' + node.name + '.' + method.name for method in node.body
                              if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                              and method.name.startswith('test'))
    return sorted(result)

def validate_result(name, discovered, result, *, skip_contract=None):
    mandatory, optional = skip_contract if skip_contract is not None else ({}, {})
    require(name == 'core' or not (mandatory or optional), 'Only full core mode may allow the exact source skip policy')
    observed = [(test.id(), reason) for test, reason in result.skipped]
    skipped = dict(observed)
    require(len(observed) == len(skipped), 'Duplicate skipped test ID')
    require(set(mandatory).issubset(skipped), 'Missing mandatory unavailable-platform/fixture skip')
    allowed = {**mandatory, **optional}
    require(all(identifier in discovered and identifier in allowed and reason == allowed[identifier]
                for identifier, reason in observed), 'Unexpected skip, reason drift or wrong platform')
    passed = [identifier for identifier in discovered if identifier not in skipped]
    require(result.testsRun == len(discovered) and result.started_ids == discovered
            and result.passed_ids == passed and result.wasSuccessful()
            and not result.expectedFailures and not result.unexpectedSuccesses,
            name + ': discovered/started/passed/skipped IDs differ, or failures/errors occurred')
    return {'group': name, **coverage_description(name), 'discovered': len(discovered), 'started': result.testsRun,
            'passed': len(result.passed_ids), 'skipped': len(skipped), 'failed': 0, 'errors': 0,
            'skipped_tests': [{'test_id': identifier, 'reason': reason} for identifier, reason in observed],
            'inventory_sha256': inventory_fingerprint(discovered)}


def coverage_description(name):
    if name == 'targeted-core':
        return {'coverage': 'targeted-core-only', 'full_core_reproduction': False,
                'full_core_inventory_count': TEST_GROUPS['core'][1],
                'not_selected_count': TEST_GROUPS['core'][1] - TARGETED_CORE_COUNT,
                'not_selected_status': 'not run; neither passed nor skipped'}
    return {'coverage': 'full-core' if name == 'core' else 'complete-installed-group',
            'full_core_reproduction': name == 'core'}


def load_group(name):
    relative = 'tests' if name == 'targeted-core' else TEST_GROUPS[name][0]
    loader = unittest.TestLoader()
    if name == 'targeted-core':
        suite = unittest.TestSuite(loader.discover(str(ROOT / relative), pattern=module + '.py')
                                   for module in TARGETED_CORE_MODULES)
    else:
        suite = loader.discover(str(ROOT / relative), pattern='test*.py')
    require(not loader.errors, 'Exact test loading failed: ' + '\n'.join(loader.errors))
    discovered = list(test_ids(suite))
    validate_inventory(name, discovered)
    return suite, discovered


def run_group(name):
    install_offline_guard()
    import socket
    try:
        socket.getaddrinfo('ci-guard.invalid', 443)
    except RuntimeError as error:
        require('Offline fixture CI' in str(error), 'Wrong offline guard failure')
    else:
        raise RuntimeError('Offline guard did not block DNS')
    skip_policy = source_skip_contract() if name == 'core' else ({}, {})
    source_group = name in {'core', 'targeted-core'}
    if source_group:
        sys.path.insert(0, str(ROOT))
    else:
        require(sys.prefix != sys.base_prefix, 'Package checks require a fresh installation')
        require(str(ROOT) not in sys.path, 'Checkout root must not shadow installed packages')
        installed_origins()
    suite, discovered = load_group(name)
    print('DISCOVERED ' + json.dumps({'group': name, **coverage_description(name),
                                     'count': len(discovered), 'test_ids': discovered}, sort_keys=True), flush=True)
    result = unittest.TextTestRunner(verbosity=2, resultclass=ExactResult, failfast=False).run(suite)
    summary = validate_result(name, discovered, result, skip_contract=skip_policy)
    if not source_group:
        installed_origins()
    print('COMPLETE ' + json.dumps(summary, sort_keys=True), flush=True)
    return summary


def table_rows(graphs):
    return {'identity': graphs['materials']['identities'], 'grade': graphs['materials']['grades'],
            'state': graphs['materials']['records'], 'property': graphs['properties']['records'],
            'source': graphs['sources']['records']}


def validate_append(candidate, before, current):
    """Reject count-preserving rewrites, partial appends, reordered rows and metadata drift."""
    wanted = deepcopy(before)
    for graph, fields in (('materials', ('identities', 'grades', 'records')),
                          ('properties', ('records',)), ('sources', ('records',))):
        for field in fields:
            previous = wanted[graph][field]
            added = candidate[graph][field]
            require(len({row['id'] for row in added}) == len(added), 'Duplicate packet record')
            require(not ({row['id'] for row in previous} & {row['id'] for row in added}), 'Packet ID already exists')
            # The established merge preserves the predecessor prefix and sorts
            # only new IDs; candidate table order is not runtime append order.
            previous.extend(sorted(deepcopy(added), key=lambda row: row['id']))
    require(current == wanted, 'Runtime differs from exact predecessor plus complete frozen append')
    require({kind: len(rows) for kind, rows in table_rows(candidate).items()} == DELTA_COUNTS,
            'Frozen packet delta changed')
    require({kind: len(rows) for kind, rows in table_rows(current).items()} == GRAPH_COUNTS,
            'Current graph counts changed')
    require(dict(Counter(row['category'] for row in current['materials']['identities'])) == PRIMARY_COUNTS,
            'Current exclusive primary categories changed')


def installation_payload():
    raw = (ROOT / PACKET_PATH).read_bytes()
    require(sha256(raw).hexdigest() == PACKET_SHA256, 'Reviewed Tian packet bytes changed')
    packet = json.loads(raw)
    require(packet['input']['baseline_sha256'] == BASELINE_HASHES, 'Packet predecessor hashes changed')
    before, current = {}, {}
    for kind, filename in (('materials', 'materials.json'), ('properties', 'reference_properties.json'), ('sources', 'sources.json')):
        old = git('show', DATA_BASE_COMMIT + ':materials_boundaries/data/' + filename)
        new = (ROOT / 'materials_boundaries/data' / filename).read_bytes()
        require(sha256(old).hexdigest() == BASELINE_HASHES[filename[:-5]], 'Predecessor resource pin differs')
        require(sha256(new).hexdigest() == RESOURCE_HASHES[filename], 'Current resource pin differs: ' + filename)
        before[kind], current[kind] = json.loads(old), json.loads(new)
    validate_append(packet['catalogs'], before, current)
    baseline = ROOT / 'experimental/platform/query-service/materials_query/pins/legacy_baseline.json'
    require(sha256(baseline.read_bytes()).hexdigest() == QUERY_BASELINE_SHA256, 'Current query baseline pin changed')
    validate_candidate_artifacts()
    preserved = {}
    for name in PRESERVED_RESOURCES:
        raw = (ROOT / name).read_bytes()
        require(raw == git('show', BASE_COMMIT + ':' + name), 'Reviewed or excluded resource changed: ' + name)
        preserved[name] = sha256(raw).hexdigest()
    examples = json.loads((ROOT / 'experimental/platform/examples/reviewed-computed-v2-second/normalized-review.json').read_bytes())
    require(len(examples['records']) == 62, 'Excluded examples acquired admission or changed count')
    manifest = json.loads((ROOT / PACKET_PATH).with_name('integration.json').read_bytes())
    validate_manifest(manifest)
    require(packet['review']['formal_admitted_delta'] == packet['report']['formal_admitted_delta'] == 0,
            'Historical candidate phase was rewritten as runtime admission')
    return {'candidate': packet['catalogs'], 'resource_hashes': RESOURCE_HASHES,
            'excluded_examples': 62, 'released_main_count': 1081,
            'delta_counts': DELTA_COUNTS, 'graph_counts': GRAPH_COUNTS,
            'primary_counts': PRIMARY_COUNTS, 'formal_counts': FORMAL_COUNTS,
            'query_baseline': QUERY_BASELINE_SHA256, 'preserved_resources': preserved,
            'packages': [package for _, _, package in PACKAGES]}


INSTALLED_SMOKE = r'''
from collections import Counter
from contextlib import redirect_stdout
from hashlib import sha256
from importlib.resources import files
import importlib
import io
import json
from pathlib import Path
import sys

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

expected = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
for name in expected['packages']:
    package = importlib.import_module(name)
    require(Path(package.__file__).resolve().is_relative_to(Path(sys.prefix).resolve()), 'Checkout package imported: ' + name)
from materials_boundaries.catalog import read_catalog, query_catalog
from materials_boundaries.cli import main
from materials_project_catalog.catalog import formal_project_catalog
from materials_query.computed_registry import baseline_digest
for name, digest in expected['resource_hashes'].items():
    require(sha256(files('materials_boundaries').joinpath('data', name).read_bytes()).hexdigest() == digest,
            'Installed catalog bytes differ: ' + name)
materials, properties, sources = (read_catalog(name) for name in ('materials', 'reference_properties', 'sources'))
tables = {'identity': materials['identities'], 'grade': materials['grades'], 'state': materials['records'],
          'property': properties['records'], 'source': sources['records']}
candidate = expected['candidate']
frozen = {'identity': candidate['materials']['identities'], 'grade': candidate['materials']['grades'],
          'state': candidate['materials']['records'], 'property': candidate['properties']['records'],
          'source': candidate['sources']['records']}
require({kind: len(rows) for kind, rows in tables.items()} == expected['graph_counts'], 'Installed graph counts differ')
require(dict(Counter(row['category'] for row in tables['identity'])) == expected['primary_counts'], 'Installed categories differ')
for kind, rows in frozen.items():
    for row in rows:
        require([value for value in tables[kind] if value['id'] == row['id']] == [row], 'Installed complete packet record differs')
facts = {'0p5wt': ('0.5 wt% Ti', '0.5', '1.7425'), '1wt': ('1 wt Ti', '1', '1.7442')}
identities = {row['id']: row for row in frozen['identity']}
states = {row['id']: row for row in frozen['state']}
properties = {row['id']: row for row in frozen['property']}
require(set(identities) == {'mat_tian2023_az31_ti_' + key for key in facts}, 'Unexpected composite identities')
for key, (label, loading, density) in facts.items():
    identity = identities['mat_tian2023_az31_ti_' + key]
    state = states['state_tian2023_az31_ti_' + key + '_as_extruded']
    prop = properties['refprop_tian2023_az31_ti_' + key + '_mass_density']
    require(identity['category'] == 'composite' and state['identity_id'] == identity['id']
            and state['grade_id'] is None and state['property_ids'] == [prop['id']]
            and prop['material_state_id'] == state['id'], 'Density identity/state/property join differs')
    require(state['source_designation'] == label, 'Literal source label changed')
    require(state['state']['composition_or_purity']['text']
            == 'Mg-3Al-1Zn (AZ31) matrix with nominal ' + loading + ' wt% nano-Ti addition.',
            'Nominal composition moved or changed')
    require(state['state']['porosity']['text'] is None
            and state['state']['porosity']['status'] == 'not_reported_in_inspected_source', 'Porosity inferred')
    require(prop['reported_value']['value_text'] == prop['reported_value']['number'] == density,
            'Printed density precision or row association changed')
require(len(frozen['identity']) == len(frozen['state']) == len(frozen['property']) == 2
        and not frozen['grade'], 'State/property/grade counts inflated identity growth')
require(frozen['source'][0]['authors'] == ['Wei Tian', 'Pengfei Gao', 'Shengli Han', 'Xiaohong Chen',
        'Fuwei Zhang', 'Yuhui Zhang', 'Tiegang Luo', 'Kaihong Zheng'], 'Eight-author attribution changed')
outputs = 0
for prop in frozen['property']:
    require(prop['evaluation_support'] == 'catalog_only' and not prop['universal_bound']
            and not prop['engineering_allowable'] and not prop['verification']['independent_scientific_review']
            and not prop['verification']['raw_data_reanalysis'], 'Density gained unsupported scientific capabilities')
    require(prop['quantity'] == 'mass_density' and prop['summary_statistic'] == 'not_stated'
            and prop['reporting_basis'] == 'not_stated' and prop['uncertainty'] is None
            and prop['uncertainty_status'] == 'not_reported_in_inspected_source'
            and prop['reported_value']['unit_code'] == 'g/cm^3'
            and prop['sample_count']['value'] is None and prop['sample_count']['relation'] == 'not_reported'
            and prop['reported_value']['unit_text'] == 'g/cm3'
            and prop['conditions']['temperature']['text'] is None
            and prop['conditions']['temperature']['status'] == 'not_reported_in_inspected_source'
            and prop['conditions']['conditioning']['text'] is None
            and prop['conditions']['test_method']['text'] == 'Digital densimeter.'
            and all(entry['fact']['status'] == 'not_reported_in_inspected_source'
                    and entry['fact']['text'] is None for entry in prop['conditions']['additional_conditions'])
            and prop['density_basis'] == 'not_stated', 'Source-qualified density semantics changed')
    selected = query_catalog('reference-properties', record_id=prop['id'])
    for language in ('en', 'zh', 'ja', 'de'):
        for flag in ('--json', '--text'):
            output = io.StringIO()
            with redirect_stdout(output):
                code = main(['catalog', 'reference-properties', '--id', prop['id'], '--lang', language, flag])
            text = output.getvalue()
            require(code == 0 and '[missing:' not in text, 'Installed density CLI failed')
            if flag == '--json':
                require(json.loads(text) == selected, 'Installed JSON depends on language')
            else:
                require(prop['reported_value']['value_text'] in text and prop['uncertainty_note'] in text,
                        'Reported density value or caveat missing from text')
            outputs += 1
require(outputs == 16, 'Expected 16 density CLI outputs with JSON equality and text value/caveat checks')
formal = formal_project_catalog()
require(formal['counts'] == expected['formal_counts'], 'Installed formal boundary changed')
for row in frozen['identity']:
    require(len([entry for entry in formal['records'] if entry['partition'] == 'legacy-source-qualified'
                 and entry['identity']['id'] == row['id']]) == 1, 'Recipe contributes multiple formal identities')
require(baseline_digest() == expected['query_baseline'], 'Installed query baseline differs')
print(json.dumps({'fresh_install': True, 'delta_counts': expected['delta_counts'],
                  'formal_counts': formal['counts'], 'graph_counts': expected['graph_counts'],
                  'selected_cli_outputs': outputs, 'query_baseline': expected['query_baseline']}))
'''


def check_installed(wheel_dir, dependency_dir):
    wheels = verify_wheels(wheel_dir)
    require(dependency_dir.is_dir() and any(dependency_dir.glob('*.whl')), 'Offline dependency wheels are missing')
    env = clean_env()
    with tempfile.TemporaryDirectory(prefix='tian-nano-ti-installed-') as temporary:
        work = Path(temporary)
        runtime = work / 'runtime'
        venv.EnvBuilder(with_pip=True, system_site_packages=False).create(runtime)
        python = runtime / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', '--find-links', dependency_dir,
             '-r', ROOT / 'experimental/platform/requirements-lock.txt',
             '-r', ROOT / 'experimental/platform/ci/projection-requirements.txt'], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', '--isolated', 'install', '--no-index', '--no-deps', *wheels], cwd=work, env=env)
        run([python, '-I', '-m', 'pip', 'check'], cwd=work, env=env)
        expected = work / 'expected.json'
        expected.write_text(json.dumps(installation_payload()), encoding='utf-8')
        smoke = work / 'installed_smoke.py'
        smoke.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n' + INSTALLED_SMOKE, encoding='utf-8')
        run([python, '-I', smoke, expected], cwd=work, env=env)
        guard = work / 'sitecustomize.py'
        guard.write_text(inspect.getsource(install_offline_guard) + '\ninstall_offline_guard()\n', encoding='utf-8')
        env['PYTHONPATH'] = str(work)
        for group in TEST_GROUPS:
            if group != 'core':
                run([python, '-I', '-B', Path(__file__).resolve(), '--installed-group', group], cwd=work, env=env)
        # Reuse the existing independent installed CLI/API/linked-fixture smoke,
        # but load the portable guard explicitly, including in CLI subprocesses.
        run([python, '-B', ROOT / 'experimental/platform/ci/check_offline.py', 'installed-smoke'], cwd=work, env=env)
    print('Complete Tian installed contract: all eight installed groups passed; '
          'no claim about source tests, live services, deployment or release.', flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument('--validate-scope', action='store_true')
    actions.add_argument('--test', action='store_true', help='Reproduce the full exact core inventory')
    actions.add_argument('--targeted-core', action='store_true',
                         help='Run only the frozen complete-module core selection, not the full core suite')
    actions.add_argument('--wheel-dir', type=Path)
    actions.add_argument('--installed-group', choices=tuple(name for name in TEST_GROUPS if name != 'core'))
    parser.add_argument('--dependency-dir', type=Path)
    args = parser.parse_args(argv)
    if args.dependency_dir and not args.wheel_dir:
        parser.error('--dependency-dir requires --wheel-dir')
    if args.installed_group:
        run_group(args.installed_group)
        return
    validate_scope()
    if args.test:
        run_group('core')
    elif args.targeted_core:
        run_group('targeted-core')
    elif args.wheel_dir:
        require(args.dependency_dir is not None, '--wheel-dir requires --dependency-dir')
        check_installed(args.wheel_dir.resolve(), args.dependency_dir.resolve())


if __name__ == '__main__':
    main()
