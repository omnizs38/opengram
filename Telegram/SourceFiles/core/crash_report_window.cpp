/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#include "core/crash_report_window.h"

#include "core/crash_reports.h"
#include "core/application.h"
#include "core/sandbox.h"
#include "window/main_window.h"
#include "platform/platform_specific.h"

#include <QtWidgets/QMenu>
#include <QtGui/QClipboard>
#include <QtGui/QContextMenuEvent>
#include <QtGui/QFontInfo>
#include <QtGui/QGuiApplication>
#include <QtGui/QScreen>
#include <QtGui/QDesktopServices>
#include <QtCore/QFileInfo>
#include <QtCore/QUrl>
#include <QtCore/QUrlQuery>

namespace {

constexpr auto kGitHubIssuesUrl = "https://github.com/omnizs38/opengram/issues/new";
constexpr auto kMinWindowWidth = 400;
constexpr auto kMaxLogInUrl = 3000;

} // namespace

PreLaunchWindow *PreLaunchWindowInstance = nullptr;

PreLaunchWindow::PreLaunchWindow(QString title) {
	setWindowIcon(Window::CreateIcon());
	setWindowFlags(Qt::Dialog | Qt::CustomizeWindowHint | Qt::WindowTitleHint | Qt::WindowCloseButtonHint);

	setWindowTitle(title.isEmpty() ? u"opengram"_q : title);

	QPalette p(palette());
	p.setColor(QPalette::Window, QColor(255, 255, 255));
	setPalette(p);

	_size = QFontInfo(font()).pixelSize();

	int paddingVertical = (_size / 2);
	int paddingHorizontal = _size;
	int borderRadius = (_size / 5);
	setStyleSheet(uR"(
QPushButton {
	padding: %1px %2px;
	background-color: #ffffff;
	border-radius: %3px;
}
QPushButton#confirm:hover,
QPushButton#cancel:hover {
	background-color: #e3f1fa;
	color: #2f9fea;
}
QPushButton#confirm {
	color: #2f9fea;
}
QPushButton#cancel {
	color: #aeaeae;
}
QLineEdit {
	border: 1px solid #e0e0e0;
	padding: 5px;
}
QLineEdit:focus {
	border: 2px solid #37a1de;
	padding: 4px;
}
)"_q.arg(paddingVertical).arg(paddingHorizontal).arg(borderRadius));
	if (!PreLaunchWindowInstance) {
		PreLaunchWindowInstance = this;
	}
}

void PreLaunchWindow::activate() {
	setWindowState(windowState() & ~Qt::WindowMinimized);
	setVisible(true);
	Platform::ActivateThisProcess();
	raise();
	activateWindow();
}

PreLaunchWindow *PreLaunchWindow::instance() {
	return PreLaunchWindowInstance;
}

PreLaunchWindow::~PreLaunchWindow() {
	if (PreLaunchWindowInstance == this) {
		PreLaunchWindowInstance = nullptr;
	}
}

PreLaunchLabel::PreLaunchLabel(QWidget *parent) : QLabel(parent) {
	QFont labelFont(font());
	labelFont.setWeight(QFont::DemiBold);
	labelFont.setPixelSize(static_cast<PreLaunchWindow*>(parent)->basicSize());
	setFont(labelFont);

	QPalette p(palette());
	p.setColor(QPalette::WindowText, QColor(0, 0, 0));
	p.setColor(QPalette::Text, QColor(0, 0, 0));
	setPalette(p);
	show();
};

void PreLaunchLabel::setText(const QString &text) {
	QLabel::setText(text);
	updateGeometry();
	resize(sizeHint());
}

void PreLaunchLabel::contextMenuEvent(QContextMenuEvent *e) {
	const auto flags = textInteractionFlags();
	const auto selectable = flags
		& (Qt::TextSelectableByMouse | Qt::TextSelectableByKeyboard);
	if (!selectable) {
		e->ignore();
		return;
	}
	const auto accel = [](QKeySequence::StandardKey key) {
		return QCoreApplication::testAttribute(
				Qt::AA_DontShowShortcutsInContextMenus)
			? QString()
			: QChar('\t')
				+ QKeySequence(key).toString(QKeySequence::NativeText);
	};
	const auto menu = new QMenu(this);
	menu->setAttribute(Qt::WA_DeleteOnClose);

	const auto copy = menu->addAction(
		u"&Copy"_q + accel(QKeySequence::Copy));
	copy->setEnabled(hasSelectedText());
	connect(copy, &QAction::triggered, this, [=] {
		if (hasSelectedText()) {
			QGuiApplication::clipboard()->setText(selectedText());
		}
	});

	menu->addSeparator();

	const auto selectAll = menu->addAction(
		u"Select All"_q + accel(QKeySequence::SelectAll));
	selectAll->setEnabled(!text().isEmpty());
	connect(selectAll, &QAction::triggered, this, [=] {
		setSelection(0, text().size());
	});

	e->accept();
	menu->popup(e->globalPos());
}

PreLaunchLog::PreLaunchLog(QWidget *parent) : QTextEdit(parent) {
	QFont logFont(font());
	logFont.setPixelSize(static_cast<PreLaunchWindow*>(parent)->basicSize());
	setFont(logFont);

	QPalette p(palette());
	p.setColor(QPalette::WindowText, QColor(96, 96, 96));
	p.setColor(QPalette::Text, QColor(96, 96, 96));
	setPalette(p);

	setReadOnly(true);
	setFrameStyle(int(QFrame::NoFrame) | QFrame::Plain);
	viewport()->setAutoFillBackground(false);
	setContentsMargins(0, 0, 0, 0);
	document()->setDocumentMargin(0);
	show();
};

PreLaunchButton::PreLaunchButton(QWidget *parent, bool confirm) : QPushButton(parent) {
	setFlat(true);

	setObjectName(confirm ? "confirm" : "cancel");

	QFont closeFont(font());
	closeFont.setWeight(QFont::DemiBold);
	closeFont.setPixelSize(static_cast<PreLaunchWindow*>(parent)->basicSize());
	setFont(closeFont);

	setCursor(Qt::PointingHandCursor);
	show();
};

void PreLaunchButton::setText(const QString &text) {
	QPushButton::setText(text);
	updateGeometry();
	resize(sizeHint());
}

NotStartedWindow::NotStartedWindow()
: _label(this)
, _log(this)
, _close(this) {
	_label.setText(u"Could not start opengram!\nYou can see complete log below:"_q);

	_log.setPlainText(Logs::full());

	connect(&_close, &QPushButton::clicked, [=] { close(); });
	_close.setText(u"CLOSE"_q);

	QRect scr(QApplication::primaryScreen()->availableGeometry());
	move(scr.x() + (scr.width() / 6), scr.y() + (scr.height() / 6));
	updateControls();
	show();
}

void NotStartedWindow::updateControls() {
	_label.show();
	_log.show();
	_close.show();

	QRect scr(QApplication::primaryScreen()->availableGeometry());
	QSize s(scr.width() / 2, scr.height() / 2);
	if (s == size()) {
		resizeEvent(0);
	} else {
		resize(s);
	}
}

void NotStartedWindow::closeEvent(QCloseEvent *e) {
	deleteLater();
	Core::Quit();
}

void NotStartedWindow::resizeEvent(QResizeEvent *e) {
	int padding = _size;
	_label.setGeometry(padding, padding, width() - 2 * padding, _label.sizeHint().height());
	_log.setGeometry(padding, padding * 2 + _label.sizeHint().height(), width() - 2 * padding, height() - 4 * padding - _label.height() - _close.height());
	_close.setGeometry(width() - padding - _close.width(), height() - padding - _close.height(), _close.width(), _close.height());
}

LastCrashedWindow::LastCrashedWindow(
	const QByteArray &crashdump,
	Fn<void()> launch)
: _label(this)
, _hint(this)
, _report(this)
, _github(this)
, _copy(this, false)
, _continue(this, false)
, _reportText(QString::fromUtf8(crashdump))
, _launch(std::move(launch)) {
	excludeReportUsername();

	_reportVersion = getReportField(qstr("Version:"));
	_reportPlatform = getReportField(qstr("Platform:"));

	const auto crashed = _reportText.contains(qstr("Caught signal"))
		|| _reportText.contains(qstr("Google Breakpad caught a crash"));
	_label.setText(crashed
		? u"Last time opengram crashed :("_q
		: u"Last time opengram was not closed properly."_q);
	_hint.setText(u"You can report this crash on GitHub. "
		"COPY LOG copies the log below."_q);

	_report.setPlainText(_reportText);

	_github.setText(u"REPORT ON GITHUB"_q);
	connect(&_github, &QPushButton::clicked, [=] { openGitHub(); });
	_copy.setText(u"COPY LOG"_q);
	connect(&_copy, &QPushButton::clicked, [=] { copyReport(); });
	_continue.setText(u"CLOSE"_q);
	connect(&_continue, &QPushButton::clicked, [=] { close(); });

	QRect scr(QApplication::primaryScreen()->availableGeometry());
	move(scr.x() + (scr.width() / 6), scr.y() + (scr.height() / 6));
	updateControls();
	show();
}

void LastCrashedWindow::copyReport() {
	QGuiApplication::clipboard()->setText(_reportText);
	_copy.setText(u"COPIED"_q);
	_hint.setText(u"The crash log is in the clipboard."_q);
	updateControls();
}

void LastCrashedWindow::openGitHub() {
	QGuiApplication::clipboard()->setText(_reportText);
	_copy.setText(u"COPIED"_q);
	_hint.setText(u"The log is copied - paste it into the issue."_q);
	QDesktopServices::openUrl(githubIssueLink());
	updateControls();
}

QString LastCrashedWindow::githubIssueLink() const {
	auto title = u"[crash] opengram"_q;
	if (!_reportVersion.isEmpty()) {
		title += ' ' + _reportVersion;
	}
	if (!_reportPlatform.isEmpty()) {
		title += u" ("_q + _reportPlatform + ')';
	}
	auto body = u"### What happened\n\n"
		"(describe what you were doing when it crashed)\n\n"
		"### Crash log\n\n"_q;
	if (_reportText.size() < kMaxLogInUrl) {
		body += u"```\n"_q + _reportText + u"\n```\n"_q;
	} else {
		body += u"(the crash log is in the clipboard - paste it here)\n"_q;
	}
	auto url = QUrl(kGitHubIssuesUrl);
	auto query = QUrlQuery();
	query.addQueryItem(u"title"_q, title);
	query.addQueryItem(u"body"_q, body);
	url.setQuery(query);
	return url.toString(QUrl::FullyEncoded);
}

QString LastCrashedWindow::getReportField(QLatin1String prefix) {
	for (const auto &line : _reportText.split('\n')) {
		const auto trimmed = line.trimmed();
		if (trimmed.startsWith(prefix)) {
			return trimmed.mid(prefix.size()).trimmed();
		}
	}
	return QString();
}

void LastCrashedWindow::excludeReportUsername() {
	// The log is meant to be published on GitHub, so the account name is
	// dropped and the local path of the minidump is shortened to its name.
	const auto usernamePrefix = qstr("Username:");
	const auto minidumpPrefix = qstr("Minidump:");
	auto lines = _reportText.split('\n');
	for (auto i = 0, l = lines.size(); i != l; ++i) {
		const auto line = lines.at(i).trimmed();
		if (line.startsWith(usernamePrefix)) {
			lines.removeAt(i);
			--i;
			--l;
		} else if (line.startsWith(minidumpPrefix)) {
			const auto path = line.mid(minidumpPrefix.size()).trimmed();
			lines[i] = u"Minidump: "_q + QFileInfo(path).fileName();
		}
	}
	_reportText = lines.join('\n');
}

void LastCrashedWindow::updateControls() {
	const auto padding = _size;
	const auto buttons = _github.width()
		+ _copy.width()
		+ _continue.width()
		+ 2 * padding;
	const auto width = std::max({
		kMinWindowWidth,
		_label.width(),
		_hint.width(),
		buttons,
	}) + 2 * padding;
	const auto contentWidth = width - 2 * padding;
	_report.resize(contentWidth, _size * 12);
	const auto height = padding
		+ _label.height()
		+ padding
		+ _hint.height()
		+ padding
		+ _report.height()
		+ padding
		+ _continue.height()
		+ padding;
	if (size() != QSize(width, height)) {
		resize(width, height);
	} else {
		resizeEvent(nullptr);
	}
}

void LastCrashedWindow::closeEvent(QCloseEvent *e) {
	deleteLater();

	if (CrashReports::Restart() == CrashReports::CantOpen) {
		new NotStartedWindow();
	} else {
		_launch();
	}
}

void LastCrashedWindow::resizeEvent(QResizeEvent *e) {
	const auto padding = _size;
	auto top = padding;
	_label.move(padding, top);
	top += _label.height() + padding;
	_hint.move(padding, top);
	top += _hint.height() + padding;
	_report.move(padding, top);
	const auto bottom = height() - padding - _continue.height();
	_github.move(padding, bottom);
	_copy.move(padding + _github.width() + padding, bottom);
	_continue.move(width() - padding - _continue.width(), bottom);
}
