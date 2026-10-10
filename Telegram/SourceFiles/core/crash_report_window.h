/*
This file is part of Telegram Desktop,
the official desktop application for the Telegram messaging service.

For license and copyright information please follow this link:
https://github.com/telegramdesktop/tdesktop/blob/master/LEGAL
*/
#pragma once

#include <QtWidgets/QLabel>
#include <QtWidgets/QTextEdit>
#include <QtWidgets/QPushButton>

class PreLaunchWindow : public QWidget {
public:
	PreLaunchWindow(QString title = QString());
	void activate();
	int basicSize() const {
		return _size;
	}
	~PreLaunchWindow();

	static PreLaunchWindow *instance();

protected:

	int _size;

};

class PreLaunchLabel : public QLabel {
public:
	PreLaunchLabel(QWidget *parent);
	void setText(const QString &text);

protected:
	void contextMenuEvent(QContextMenuEvent *e) override;

};

class PreLaunchLog : public QTextEdit {
public:
	PreLaunchLog(QWidget *parent);

};

class PreLaunchButton : public QPushButton {
public:
	PreLaunchButton(QWidget *parent, bool confirm = true);
	void setText(const QString &text);

};

class NotStartedWindow : public PreLaunchWindow {
public:
	NotStartedWindow();

protected:
	void closeEvent(QCloseEvent *e) override;
	void resizeEvent(QResizeEvent *e) override;

private:
	void updateControls();

	PreLaunchLabel _label;
	PreLaunchLog _log;
	PreLaunchButton _close;

};

// opengram: shown after a crash or an unclean shutdown. It never sends
// anything anywhere - it offers the log for copying and a link to the
// GitHub issue form, so the user decides what to publish.
class LastCrashedWindow : public PreLaunchWindow {

public:
	LastCrashedWindow(const QByteArray &crashdump, Fn<void()> launch);

	void copyReport();
	void openGitHub();

protected:
	void closeEvent(QCloseEvent *e) override;
	void resizeEvent(QResizeEvent *e) override;

private:
	void updateControls();
	void excludeReportUsername();

	[[nodiscard]] QString getReportField(QLatin1String prefix);
	[[nodiscard]] QString githubIssueLink() const;

	PreLaunchLabel _label, _hint;
	PreLaunchLog _report;
	PreLaunchButton _github, _copy, _continue;

	QString _reportText, _reportVersion, _reportPlatform;

	Fn<void()> _launch;

};
