#!/usr/bin/env python3

# opengram release helper.
#
# opengram has no semantic versions: its version IS a build number. Every
# release increments OpengramBuild in Telegram/SourceFiles/core/version.h by
# one, the interface shows "<build> (<Telegram Desktop base version>)" and the
# version link opens https://github.com/omnizs38/opengram/releases/tag/v<build>.
#
# A release goes like this:
#
#   python Telegram/build/opengram_release.py bump
#   build-opengram.bat
#   python Telegram/build/opengram_release.py publish --push --gh --asset out\Release\opengram.exe
#
# "bump" is the only command that changes the repository. "publish" tags HEAD,
# writes the release notes next to the repository (so they never show up in
# git status) and, with --gh, creates the GitHub release itself.

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

scriptPath = Path(__file__).resolve().parent
repoPath = scriptPath.parents[1]
versionHeader = repoPath / 'Telegram' / 'SourceFiles' / 'core' / 'version.h'
versionFile = scriptPath / 'version'
changelogFile = repoPath / 'changelog.txt'

buildRe = re.compile(r'(constexpr auto OpengramBuild = )(\d+)(;)')
baseRe = re.compile(r'^AppVersionStr\s+(\S+)\s*$', re.M)


def fail(message):
    print('Error: ' + message)
    sys.exit(1)


def run(args, quiet=False):
    # Run a command in the repository and capture its output.
    result = subprocess.run(
        [str(a) for a in args],
        cwd=repoPath,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    if result.returncode != 0:
        if not quiet:
            if result.stdout.strip():
                print(result.stdout.strip())
            fail('command failed: ' + ' '.join(str(a) for a in args))
        return ''
    return result.stdout.strip()


def runOk(args):
    # Run a command in the repository with its output left on the screen.
    result = subprocess.run([str(a) for a in args], cwd=repoPath)
    return result.returncode == 0


def readBuild():
    match = buildRe.search(versionHeader.read_text(encoding='utf-8'))
    if not match:
        fail('OpengramBuild not found in ' + str(versionHeader))
    return int(match.group(2))


def writeBuild(build):
    text = versionHeader.read_text(encoding='utf-8')
    text = buildRe.sub(
        lambda m: m.group(1) + str(build) + m.group(3),
        text,
        count=1)
    versionHeader.write_text(text, encoding='utf-8')


def parseBase(text):
    match = baseRe.search(text or '')
    return match.group(1) if match else None


def readBase():
    return parseBase(versionFile.read_text(encoding='utf-8'))


def readBaseAt(ref):
    return parseBase(run(['git', 'show', ref + ':Telegram/build/version'],
        quiet=True))


def lastTag():
    return run(['git', 'describe', '--tags', '--abbrev=0', '--match', 'v*'],
        quiet=True) or None


def tagExists(tag):
    return bool(run(['git', 'tag', '-l', tag], quiet=True))


def commitSubjects(revRange):
    result = run(['git', 'log', '--no-merges', '--pretty=format:%s', revRange],
        quiet=True)
    return [
        line for line in result.splitlines()
        if line.strip() and not line.startswith('release: opengram')
    ]


def upstreamChangelog(base):
    # changelog.txt is Telegram's own changelog and keeps its upstream format,
    # because set_version.py and changelog2appstream.py parse it. Its entries
    # are exactly what the "Telegram Desktop" part of the release notes needs.
    if not changelogFile.exists():
        return []
    lines = changelogFile.read_text(encoding='utf-8').splitlines()
    for wanted in (base, '.'.join(base.split('.')[:2])):
        entries = []
        inside = False
        for line in lines:
            if re.match(r'^' + re.escape(wanted) + r'\s', line):
                inside = True
                continue
            if inside:
                if line.startswith('- '):
                    entries.append(line[2:].strip())
                elif line.strip() and not line.startswith((' ', '\t')):
                    break
        if entries:
            return entries
    return []


def buildNotes(build, base, previousBase, revRange):
    lines = [
        '**opengram ' + str(build) + '** - based on Telegram Desktop ' + base,
        '',
        '### Changes in opengram',
        '',
    ]
    subjects = commitSubjects(revRange)
    lines += ['- ' + s for s in subjects] if subjects else ['- Maintenance release.']
    if previousBase != base:
        lines += ['', '### Telegram Desktop ' + base + ' (upstream base)', '']
        upstream = upstreamChangelog(base)
        if upstream:
            lines += ['- ' + entry for entry in upstream]
        else:
            lines.append('<!-- Paste the ' + base
                + ' section from changelog.txt here. -->')
    return '\n'.join(lines) + '\n'


def doStatus(args):
    build = readBuild()
    base = readBase()
    tag = 'v' + str(build)
    print('opengram %d (Telegram %s)' % (build, base))
    print('tag %s: %s' % (tag, 'exists' if tagExists(tag) else 'missing'))
    return 0


def doBump(args):
    if run(['git', 'status', '--porcelain'], quiet=True):
        fail('the working tree is not clean, commit or stash your changes first')
    build = readBuild() + 1
    base = readBase()
    writeBuild(build)
    print('opengram %d (Telegram %s)' % (build, base))
    if args.no_commit:
        print('version.h updated, left uncommitted')
        return 0
    runOk(['git', 'add', versionHeader])
    if not runOk(['git', 'commit', '-m',
            'release: opengram %d (Telegram %s)' % (build, base)]):
        run(['git', 'checkout', 'HEAD', '--', versionHeader], quiet=True)
        fail('the release commit failed, version.h was restored')
    print('Now build the release, then run "publish".')
    return 0


def doPublish(args):
    build = readBuild()
    base = readBase()
    tag = 'v' + str(build)
    if tagExists(tag):
        fail('tag %s already exists' % tag)
    previous = lastTag()
    previousBase = readBaseAt(previous) if previous else None
    notes = buildNotes(
        build,
        base,
        previousBase,
        (previous + '..HEAD') if previous else 'HEAD')
    notesPath = (Path(args.notes_out) if args.notes_out
        else repoPath.parent / ('release-notes-' + tag + '.md'))
    notesPath.write_text(notes, encoding='utf-8')
    if not runOk(['git', 'tag', '-a', tag, '-m',
            'opengram %d (Telegram %s)' % (build, base)]):
        fail('could not create tag ' + tag)
    print('Tagged %s, release notes: %s' % (tag, notesPath))
    if args.push:
        if not runOk(['git', 'push', 'origin', args.branch]):
            fail('could not push ' + args.branch)
        if not runOk(['git', 'push', 'origin', tag]):
            fail('could not push ' + tag)
    else:
        print('Push with: git push origin %s && git push origin %s'
            % (args.branch, tag))
    if args.gh:
        if not args.push:
            fail('--gh requires --push')
        if not shutil.which('gh'):
            fail('the GitHub CLI "gh" is not installed')
        command = ['gh', 'release', 'create', tag,
            '--title', 'opengram %d (Telegram %s)' % (build, base),
            '--notes-file', notesPath]
        command += [Path(asset).resolve() for asset in args.asset]
        if not runOk(command):
            fail('could not create the GitHub release')
        print('GitHub release %s created.' % tag)
    return 0


def main():
    parser = argparse.ArgumentParser('opengram release helper')
    commands = parser.add_subparsers(dest='command', required=True)

    status = commands.add_parser('status', help='show the current build number')
    status.set_defaults(func=doStatus)

    bump = commands.add_parser('bump', help='increment the build number')
    bump.add_argument('--no-commit', action='store_true',
        help='only edit version.h, do not commit')
    bump.set_defaults(func=doBump)

    publish = commands.add_parser('publish',
        help='tag the current build and prepare release notes')
    publish.add_argument('--push', action='store_true',
        help='push the branch and the tag to origin')
    publish.add_argument('--gh', action='store_true',
        help='create the GitHub release with gh (requires --push)')
    publish.add_argument('--asset', action='append', default=[],
        help='file to attach to the GitHub release, repeatable')
    publish.add_argument('--branch', default='opengram',
        help='branch to push, defaults to opengram')
    publish.add_argument('--notes-out',
        help='where to write the release notes')
    publish.set_defaults(func=doPublish)

    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
