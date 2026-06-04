#!/usr/bin/env bash
set -euo pipefail

RAW_BASE="${AGENT_WORKSPACE_RAW_BASE:-https://raw.githubusercontent.com/adiacov/agent-workspace/main}"
TEMPLATE_SOURCE_DIR="${AGENT_WORKSPACE_TEMPLATE_SOURCE_DIR:-}"

CORE_TEMPLATE_FILES=(
  "default/.gitignore"
  "default/STATE.md"
  "default/BRAINSTORM.md"
  "default/WORKFLOWS.md"
  "adapters/pi/AGENTS.md"
  "adapters/codex/AGENTS.md"
  "adapters/claude/CLAUDE.md"
  "adapters/cursor/.cursor/rules/agent-workspace.mdc"
  "adapters/custom/INSTRUCTIONS.md"
)

SOFTWARE_PROFILE_TEMPLATE_FILES=(
  "profiles/software/ENGINEERING.md"
)

say() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# Agent selection can come from command-line arguments, environment variables,
# or the interactive prompt. CLI args intentionally have highest precedence so
# agents can run the curl bootstrap non-interactively, for example:
#   curl -fsSL .../bootstrap.sh | bash -s -- --agents claude
SELECTED_AGENTS="${AGENT_WORKSPACE_AGENTS:-}"
CUSTOM_OUTPUT_PATH="${AGENT_WORKSPACE_CUSTOM_PATH:-}"
WORKSPACE_PROFILE="${AGENT_WORKSPACE_PROFILE:-}"
PROMPT_VALUE=""
COMMAND="init"
AGENTS_FROM_CLI=0

can_prompt() {
  # The bootstrap script is commonly piped from curl, so stdin is the script body.
  # Read prompts from /dev/tty instead of stdin to keep interactive use possible.
  { true < /dev/tty > /dev/tty; } 2>/dev/null
}

prompt_line() {
  printf '%s\n' "$*" >&2
}

prompt_read() {
  local prompt="$1"
  PROMPT_VALUE=""
  printf '%s' "$prompt" >&2
  IFS= read -r PROMPT_VALUE < /dev/tty
}

script_path() {
  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P
  else
    return 1
  fi
}

copy_skip() {
  # Generated files are never overwritten automatically. This keeps bootstrap safe
  # to rerun and avoids destroying local project-specific instructions or memory.
  local src="$1" dst="$2"
  if [ -e "$dst" ]; then
    say "skip existing $dst"
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  say "created $dst"
}

download_file() {
  local rel="$1" dst="$2"
  command -v curl >/dev/null 2>&1 || die "curl is required to download templates"
  mkdir -p "$(dirname "$dst")"
  curl -fsSL "$RAW_BASE/templates/$rel" -o "$dst"
}

resolve_template_source() {
  if [ -n "$TEMPLATE_SOURCE_DIR" ]; then
    [ -d "$TEMPLATE_SOURCE_DIR" ] || die "template source not found: $TEMPLATE_SOURCE_DIR"
    printf '%s\n' "$TEMPLATE_SOURCE_DIR"
    return 0
  fi

  local dir
  if dir="$(script_path 2>/dev/null)"; then
    if [ -d "$dir/templates" ]; then
      printf '%s\n' "$dir/templates"
      return 0
    fi
    if [ -d "$dir/../templates" ]; then
      (cd "$dir/../templates" && pwd -P)
      return 0
    fi
  fi

  return 1
}

install_templates() {
  # Keep a local template cache so future ./bin/agent-workspace add-agent calls
  # work without depending on the source repository layout.
  local dst_root=".agent/templates"
  mkdir -p "$dst_root"

  local template_files=("${CORE_TEMPLATE_FILES[@]}")
  if [ "$WORKSPACE_PROFILE" = "code" ]; then
    template_files+=("${SOFTWARE_PROFILE_TEMPLATE_FILES[@]}")
  fi

  local src_root=""
  if src_root="$(resolve_template_source 2>/dev/null)"; then
    for rel in "${template_files[@]}"; do
      [ -f "$src_root/$rel" ] || die "missing template: $src_root/$rel"
      copy_skip "$src_root/$rel" "$dst_root/$rel"
    done
  else
    local tmp
    tmp="$(mktemp -d)"
    for rel in "${template_files[@]}"; do
      download_file "$rel" "$tmp/$rel"
      copy_skip "$tmp/$rel" "$dst_root/$rel"
    done
    rm -rf "$tmp"
  fi
}

ensure_git() {
  command -v git >/dev/null 2>&1 || die "git is required"
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local top current
    top="$(git rev-parse --show-toplevel)"
    top="$(cd "$top" && pwd -P)"
    current="$(pwd -P)"
    if [ "$top" != "$current" ]; then
      die "current directory is inside another git repository: $top. Run from the project root or outside any existing repository."
    fi
    return 0
  fi
  git init
}

generate_defaults() {
  [ -d ".agent/templates/default" ] || die "missing .agent/templates/default"
  local file rel
  while IFS= read -r -d '' file; do
    rel="${file#.agent/templates/default/}"
    copy_skip "$file" "$rel"
  done < <(find .agent/templates/default -type f -print0)
}

generate_profile_files() {
  case "$WORKSPACE_PROFILE" in
    general) return 0 ;;
    code)
      local src=".agent/templates/profiles/software/ENGINEERING.md"
      [ -f "$src" ] || die "missing code profile template: $src"
      copy_skip "$src" "ENGINEERING.md"
      ;;
    *) die "unsupported workspace profile: $WORKSPACE_PROFILE" ;;
  esac
}

install_cli() {
  mkdir -p bin
  if [ -e "bin/agent-workspace" ]; then
    say "skip existing bin/agent-workspace"
    return 0
  fi

  if [ -n "${BASH_SOURCE[0]:-}" ] && [ -f "${BASH_SOURCE[0]}" ]; then
    cp "${BASH_SOURCE[0]}" bin/agent-workspace
  else
    command -v curl >/dev/null 2>&1 || die "curl is required to install bin/agent-workspace"
    curl -fsSL "$RAW_BASE/bootstrap.sh" -o bin/agent-workspace
  fi
  chmod +x bin/agent-workspace
  say "created bin/agent-workspace"
}

adapter_destination() {
  case "$1" in
    pi) printf '%s\n' "AGENTS.md" ;;
    codex) printf '%s\n' "AGENTS.md" ;;
    claude) printf '%s\n' "CLAUDE.md" ;;
    cursor) printf '%s\n' ".cursor/rules/agent-workspace.mdc" ;;
    *) return 1 ;;
  esac
}

adapter_template() {
  case "$1" in
    pi) printf '%s\n' ".agent/templates/adapters/pi/AGENTS.md" ;;
    codex) printf '%s\n' ".agent/templates/adapters/codex/AGENTS.md" ;;
    claude) printf '%s\n' ".agent/templates/adapters/claude/CLAUDE.md" ;;
    cursor) printf '%s\n' ".agent/templates/adapters/cursor/.cursor/rules/agent-workspace.mdc" ;;
    *) return 1 ;;
  esac
}

generate_adapter() {
  local agent="$1" src dst
  src="$(adapter_template "$agent")" || die "unknown agent: $agent"
  dst="$(adapter_destination "$agent")" || die "unknown agent: $agent"
  [ -f "$src" ] || die "missing adapter template: $src"
  copy_skip "$src" "$dst"
}

validate_custom_path() {
  local dst="$1"
  case "$dst" in
    /*|*..*) die "custom path must be project-root-relative and must not contain .." ;;
  esac
}

generate_custom_adapter() {
  local src=".agent/templates/adapters/custom/INSTRUCTIONS.md"
  [ -f "$src" ] || die "missing custom adapter template: $src"

  local dst="${CUSTOM_OUTPUT_PATH:-INSTRUCTIONS.md}"
  validate_custom_path "$dst"
  copy_skip "$src" "$dst"
}

parse_args() {
  # Supported input precedence:
  #   1. CLI args, e.g. --agents claude
  #   2. AGENT_WORKSPACE_AGENTS / AGENT_WORKSPACE_CUSTOM_PATH env vars
  #   3. Interactive prompt
  # This preserves human-friendly bootstrap while enabling agent-friendly,
  # non-interactive initialization.
  if [ "$#" -gt 0 ]; then
    case "$1" in
      init|add-agent|status|help)
        COMMAND="$1"
        shift
        ;;
      -h|--help)
        COMMAND="help"
        shift
        ;;
    esac
  fi

  while [ "$#" -gt 0 ]; do
    case "$1" in
      --agents)
        shift
        [ "$#" -gt 0 ] || die "--agents requires a value"
        SELECTED_AGENTS="$1"
        AGENTS_FROM_CLI=1
        shift
        ;;
      --agents=*)
        SELECTED_AGENTS="${1#--agents=}"
        [ -n "$SELECTED_AGENTS" ] || die "--agents requires a value"
        AGENTS_FROM_CLI=1
        shift
        ;;
      --custom-path)
        shift
        [ "$#" -gt 0 ] || die "--custom-path requires a value"
        CUSTOM_OUTPUT_PATH="$1"
        shift
        ;;
      --custom-path=*)
        CUSTOM_OUTPUT_PATH="${1#--custom-path=}"
        [ -n "$CUSTOM_OUTPUT_PATH" ] || die "--custom-path requires a value"
        shift
        ;;
      --profile)
        shift
        [ "$#" -gt 0 ] || die "--profile requires a value"
        WORKSPACE_PROFILE="$1"
        shift
        ;;
      --profile=*)
        WORKSPACE_PROFILE="${1#--profile=}"
        [ -n "$WORKSPACE_PROFILE" ] || die "--profile requires a value"
        shift
        ;;
      --)
        shift
        [ "$#" -eq 0 ] || die "unexpected argument after --: $1"
        ;;
      *)
        if [ "$COMMAND" = "add-agent" ] && [ -z "$SELECTED_AGENTS" ]; then
          SELECTED_AGENTS="$1"
          AGENTS_FROM_CLI=1
          shift
        else
          die "unknown argument: $1"
        fi
        ;;
    esac
  done
}

validate_profile() {
  case "$WORKSPACE_PROFILE" in
    general|code) ;;
    software)
      warn "workspace profile 'software' is deprecated; use 'code'"
      WORKSPACE_PROFILE="code"
      ;;
    *) die "invalid workspace profile: $WORKSPACE_PROFILE (supported: general, code)" ;;
  esac
}

select_profile() {
  if [ -n "$WORKSPACE_PROFILE" ]; then
    validate_profile
    return 0
  fi

  if can_prompt; then
    prompt_read 'Workspace profile [general/code] (default: general): '
    WORKSPACE_PROFILE="${PROMPT_VALUE:-general}"
  else
    WORKSPACE_PROFILE="general"
  fi

  validate_profile
}

select_agents() {
  if [ -n "$SELECTED_AGENTS" ]; then
    return 0
  fi

  can_prompt || die "cannot prompt for agent selection. Run in an interactive terminal or pass --agents, for example: curl -fsSL $RAW_BASE/bootstrap.sh | bash -s -- --agents claude"

  prompt_line "Select agent adapters to generate:"
  prompt_line "  pi, codex, claude, cursor, custom"
  prompt_read 'Agents (comma/space separated, blank for none): '
  SELECTED_AGENTS="$PROMPT_VALUE"
}

validate_agents_selection() {
  local selected="$1" token
  selected="${selected//,/ }"

  for token in $selected; do
    case "$token" in
      pi|codex|claude|cursor|custom|none|None|NONE) ;;
      *) die "unknown agent selection: $token" ;;
    esac
  done
}

selection_has_custom() {
  local selected=" ${1//,/ } "
  case "$selected" in
    *" custom "*) return 0 ;;
    *) return 1 ;;
  esac
}

collect_custom_path() {
  if [ -n "$CUSTOM_OUTPUT_PATH" ]; then
    validate_custom_path "$CUSTOM_OUTPUT_PATH"
    return 0
  fi

  if [ "$AGENTS_FROM_CLI" -eq 1 ]; then
    CUSTOM_OUTPUT_PATH="INSTRUCTIONS.md"
    validate_custom_path "$CUSTOM_OUTPUT_PATH"
    return 0
  fi

  can_prompt || die "cannot prompt for custom instruction file. Set AGENT_WORKSPACE_CUSTOM_PATH or pass --custom-path, for example: --custom-path INSTRUCTIONS.md"

  prompt_read 'Custom instruction file [INSTRUCTIONS.md]: '
  CUSTOM_OUTPUT_PATH="${PROMPT_VALUE:-INSTRUCTIONS.md}"
  validate_custom_path "$CUSTOM_OUTPUT_PATH"
}

run_selected_agents() {
  local selected="$1" token
  selected="${selected//,/ }"

  for token in $selected; do
    case "$token" in
      pi|codex|claude|cursor) generate_adapter "$token" ;;
      custom) generate_custom_adapter ;;
      none|None|NONE) ;;
      *) die "unknown agent selection: $token" ;;
    esac
  done
}

add_agent() {
  [ -d ".agent/templates" ] || die "missing .agent/templates. Run ./bin/agent-workspace init or bootstrap again to install templates."

  if [ "$#" -gt 0 ]; then
    SELECTED_AGENTS="$1"
  else
    select_agents
  fi

  validate_agents_selection "$SELECTED_AGENTS"
  if selection_has_custom "$SELECTED_AGENTS"; then
    collect_custom_path
  fi

  run_selected_agents "$SELECTED_AGENTS"
}

init() {
  select_profile
  select_agents
  validate_agents_selection "$SELECTED_AGENTS"
  if selection_has_custom "$SELECTED_AGENTS"; then
    collect_custom_path
  fi

  ensure_git
  install_templates
  generate_defaults
  generate_profile_files
  install_cli
  add_agent "$SELECTED_AGENTS"
}

status_one() {
  if [ -e "$1" ]; then
    printf 'present  %s\n' "$1"
  else
    printf 'missing  %s\n' "$1"
  fi
}

status() {
  status_one ".agent/templates"
  status_one "bin/agent-workspace"
  status_one ".gitignore"
  status_one "STATE.md"
  status_one "BRAINSTORM.md"
  status_one "AGENTS.md"
  status_one "CLAUDE.md"
  status_one ".cursor/rules/agent-workspace.mdc"
}

usage() {
  cat <<'USAGE'
Usage: agent-workspace [init|add-agent|status|help] [options]

Options:
  --agents AGENTS       Comma/space separated agents: pi, codex, claude, cursor, custom
  --custom-path PATH    Output path used with --agents custom
  --profile PROFILE     Workspace profile: general, code (default: general)

With no command, runs init. The curl bootstrap command also runs init.

Examples:
  agent-workspace init --agents claude
  agent-workspace init --profile code --agents pi
  agent-workspace init --profile general
  AGENT_WORKSPACE_PROFILE=code agent-workspace init
  agent-workspace add-agent --agents cursor
  agent-workspace add-agent cursor
USAGE
}

parse_args "$@"
case "$COMMAND" in
  init) init ;;
  add-agent) add_agent ;;
  status) status ;;
  help) usage ;;
  *) usage >&2; exit 1 ;;
esac
