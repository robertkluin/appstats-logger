"""
Does the job of linking up the packages listed in requirements.txt and adding
them to the lib directory for deploying to appspot.
"""

import os

import pip
from pip.req import parse_requirements

BASE_PATH = 'lib'


def get_required_packages():
    return [p.name for p in parse_requirements('requirements.txt')]


def get_distributions(*packages):
    for installed_dist in pip.get_installed_distributions():
        if installed_dist.project_name not in packages:
            continue

        yield installed_dist


def get_module_meta(*packages):
    """
    Produces the module name and its location for the installed packages
    """
    distributions = {}
    seen = set()

    for dist in get_distributions(*packages):
        distributions[dist.key] = dist
        seen.add(dist.project_name)

        filename = dist.key
        if not os.path.exists(os.path.join(dist.location, dist.key)):
            loc = os.path.join(
                dist.location, dist.egg_name() + '.egg-info', 'top_level.txt')
            fp = open(loc, 'r')
            filename = fp.readline().rstrip('\n')
            fp.close()

            if not os.path.exists(os.path.join(dist.location, filename)):
                filename += ".py"

        yield filename, dist.location

    not_seen = seen.difference(packages)

    if not_seen:
        raise EnvironmentError('Distributions %r not found' % (
            ', '.join(not_seen)))


def _rmdir(dest_dir):
    """
    Removes a directory, supporting symlinks
    """
    if not os.path.exists(dest_dir):
        return

    try:
        os.unlink(dest_dir)
    except OSError:
        # probably a directory
        import shutil

        shutil.rmtree(dest_dir)


def ensure_symlink(location, module, dest_root=BASE_PATH):
    source_dir = os.path.join(location, module)
    dest_dir = os.path.join(dest_root, module)

    if not os.path.exists(source_dir):
        raise OSError('Source package %r not found' % (source_dir,))

    os.symlink(source_dir, dest_dir)


if __name__ == '__main__':
    if not os.path.exists(BASE_PATH):
        os.mkdir(BASE_PATH)

    for path in os.listdir(BASE_PATH):
        _rmdir(os.path.join(BASE_PATH, path))

    for module, location in get_module_meta(*get_required_packages()):
        ensure_symlink(location, module)

