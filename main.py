__author__ = 'n3tn0'
__version__ = 'ALPHA'

from PyQt5.QtWidgets import *
from ui import Ui_MainWindow
import sys, os, shutil
from subprocess import call

class MainWindow(QMainWindow, Ui_MainWindow):
    vcsdir = 'vcsprotos'
    progpath = os.path.dirname(os.path.realpath('Makefile'))
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        # Define buttons
        self.startwrite.clicked.connect(self.writepkgbuild)
        self.installbrowse.clicked.connect(self.selectinstallfile)
        self.desktopbrowse.clicked.connect(self.selectdesktopfile)
        self.savepkgbutton.clicked.connect(self.savepkg)
        self.savesrcbutton.clicked.connect(self.savesrc)
        self.upload.clicked.connect(self.uploadtoaur)

    def combinepkgnames(self, text):
        packages = []
        for i in text.split('\n'):
            packages.append('\'%s\'')
        return ' '.join(packages)

    def selectinstallfile(self):
        installfile = QFileDialog.getOpenFileName(self, 'Select .install file')
        self.source_install.setText(installfile[0])

    def selectdesktopfile(self):
        desktopfile = QFileDialog.getOpenFileName(self, 'Select .desktop file')
        self.source_desktop.setText(desktopfile[0])

    def writepkgbuild(self):
        os.chdir(self.progpath)
        # Open a file for writing to
        try:
            os.mkdir('/tmp/qtpkg')
        except FileExistsError:
            shutil.rmtree('/tmp/qtpkg')
            os.mkdir('/tmp/qtpkg')
        '''Fix to pacakage name or program name, make path a variable to reduce redundancy'''

        # Get form values and assign them to their lines
        lines = []
        lines.append('# Created with UNAMED')
        lines.append('# Maintained by %s' % self.maintainer.text())
        lines.append('pkgname=\'%s\'' % self.pkgname.text())
        lines.append('pkgver=%s' % (self.pkgver.text()))
        lines.append('pkgrel=1')
        lines.append('pkgdesc=\'%s\'' % (self.pkgdesc.text()))
        lines.append('url=\'%s\'' % self.pkgurl.text())
        lines.append('arch=\'x86_64 i686\'') #Add this!
        lines.append('license=\'%s\'' % (self.license.currentText()))
        lines.append('depends=(%s)' % self.combinepkgnames(self.deps.toPlainText()))
        lines.append('makedepends=(%s)' % self.combinepkgnames(self.makedeps.toPlainText()))
        lines.append('optdepends=(%s)' % self.combinepkgnames(self.optdeps.toPlainText()))
        lines.append('provides=(%s)' % self.combinepkgnames(self.provides.toPlainText()))
        lines.append('conflicts=(%s)' % self.combinepkgnames(self.conflicts.toPlainText()))
        lines.append('replaces=(%s)' % self.combinepkgnames(self.replaces.toPlainText()))

        if self.source_install.text() != '':
            lines.append('install=\'%s\'') % '%s.install' % self.pkgname.text()

        # Determine how the rest of the PKGBUILD will be set up and set up VCS specific variables
        if self.packagetype.currentText() == 'Git':
            prefix = 'git'
            lines.append('_gitroot=%s' % self.source_package.text())
            bi = self.source_package.text().find('#')
            if bi == -1:
                lines.append('_gitname=master')
            else:
                lines.append('_gitname=%s' % self.source_package.text()[bi+1:])
        elif self.packagetype.currentText() == 'Subversion':
            prefix = 'svn'
            lines.append('_svntrunk=%s' % self.source_package.text())
            bi = self.source_package.text().find('#')
            if bi == -1:
                lines.append('_svnmod=master')
            else:
                lines.append('_svnmod=%s' % self.source_package.text()[bi+1:])
        elif self.packagetype.currentText() == 'Mercurial':
            prefix = 'hg'
            lines.append('_hgroot=%s' % self.source_package.text())
            bi = self.source_package.text().find('#')
            if bi == -1:
                lines.append('_hgrepo=master')
            else:
                lines.append('_hgrepo=%s' % self.source_package.text()[bi+1:])
        elif self.packagetype.currentText() == 'Bazaar':
            prefix = 'bzr'
            lines.append('_bzrtrunk=%s' % self.source_package.text())
            bi = self.source_package.text().find('#')
            if bi == -1:
                lines.append('_bzrmod=master')
            else:
                lines.append('_bzrmod=%s' % self.source_package.text()[bi+1:])
        else:
            prefix = 'normal'

        # Add appropriate prefix to pkgname
        global name
        name = self.pkgname.text()
        if prefix != 'normal':
            name += '-%s' % prefix
            lines[2] = 'pkgname=\'%s\'' % name
            if self.source_install.text() != '':
                lines[15] = 'install=\'%s.install\'' % name

        # Make source line
        sources = []
        pkgurl = self.source_package.text()
        if prefix != 'normal':
            pkgurl = prefix + pkgurl
        sources.append('\'%s\'' % pkgurl)
        if self.source_desktop.text() != '':
            sources.append('%s.desktop' % self.pkgname.text())
        lines.append('sources=(%s)' % '\n'.join(sources))
        lines.append('md5sums=()\n\n')

        with open(self.vcsdir + '/' + prefix, 'rt') as p2:
            part2 = p2.readlines()
            with open('/tmp/qtpkg/PKGBUILD', 'a+') as final:
                final.writelines('\n'.join(lines))
                final.writelines(part2)

        os.chdir('/tmp/qtpkg/')
        call(['updpkgsums'])

        # Move the PKGBUILD to the correct place
        try:
            os.mkdir('%s/abs' % os.path.expanduser('~'))
        except FileExistsError:
            pass
        try:
            os.mkdir('%s/abs/%s' % (os.path.expanduser('~'), name))
        except FileExistsError:
            pass
        shutil.copyfile('/tmp/qtpkg/PKGBUILD', '%s/abs/%s/PKGBUILD' % (os.path.expanduser('~'), name))

        QMessageBox.information(self, 'Success!', '<p align=center> PKGBUILD successfully generated and saved to %s/abs/%s/' % (os.path.expanduser('~'), name))

    def preparesavepkg(self):
        # Generate PKGBUILD
        self.writepkgbuild()

        # Copy install, desktop files if applicable
        if self.source_install.text() != '':
            shutil.copyfile(self.source_install.text(), '%s/abs/%s/%s.install' % (os.path.expanduser('~'), name, name))
        if self.source_desktop.text() != '':
            shutil.copyfile(self.source_install.text(), '%s/abs/%s/%s.desktop' % (os.path.expanduser('~'), name, name))


    def savesrc(self):
        self.preparesavepkg()
        # Generate .src.tar.gz
        os.chdir('%s/abs/%s/' % (os.path.expanduser('~'), name))
        call(['makepkg', '-S'])

        QMessageBox.information(self, 'Success!', '<p align=center> %s.src.tar.xz successfully generated and saved to %s/abs/%s/' % (name, os.path.expanduser('~'), name))

    def savepkg(self):
        self.preparesavepkg()
        # Generate .pkg.tar.gz
        os.chdir('%s/abs/%s/' % (os.path.expanduser('~'), name))
        call(['makepkg', '--allsource'])

        QMessageBox.information(self, 'Success!', '<p align=center> %s.pkg.tar.xz successfully generated and saved to %s/abs/%s/' % (name, os.path.expanduser('~'), name))

    def uploadtoaur(self):
        self.writepkgbuild()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()

main()