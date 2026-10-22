#pragma once

#include <QComboBox>
#include <QCoreApplication>
#include <QMessageBox>
#include <QLocale>
#include <QSettings>
#include <QString>
#include <QTranslator>
#include <QWidget>

// A single explicit preference is more dependable than the locale forwarded
// through pkexec (which may be C/POSIX even on a French desktop).
namespace HarborLanguage {
inline QString normalize(const QString &code)
{
    const QString language = code.trimmed().replace(QLatin1Char('-'), QLatin1Char('_'));
    if (language == QLatin1String("fr_FR") || language == QLatin1String("fr") ||
        language.startsWith(QLatin1String("fr_"))) return QStringLiteral("fr_FR");
    if (language == QLatin1String("zh_CN") || language == QLatin1String("zh") ||
        language.startsWith(QLatin1String("zh_"))) return QStringLiteral("zh_CN");
    return QStringLiteral("en_US");
}

inline QString selected(const QString &systemCode = QLocale::system().name())
{
    QSettings prefs(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
    const QString saved = prefs.value(QStringLiteral("ui/language")).toString();
    return normalize(saved.isEmpty() ? systemCode : saved);
}

inline bool loadCatalog(QTranslator &translator, const QString &language, const QString &directory)
{
    if (normalize(language) == QLatin1String("en_US")) return true; // English source
    return translator.load(QStringLiteral("btrfsassistant_") + normalize(language), directory);
}

// The choices use native names so they remain recognizable in any UI locale.
// Translations of all screens take effect upon the next application launch,
// avoiding a partial retranslation of in-progress backup/recovery controls.
inline QComboBox *createSelector(QWidget *parent, bool showConfirmation = true)
{
    auto *selector = new QComboBox(parent);
    selector->setObjectName(QStringLiteral("harborLanguageSelector"));
    selector->setAccessibleName(QCoreApplication::translate("HarborLanguage", "Interface language"));
    selector->setToolTip(QCoreApplication::translate("HarborLanguage",
        "Choose English, French or Simplified Chinese. Reopen Harbor to apply."));
    selector->addItem(QStringLiteral("English"), QStringLiteral("en_US"));
    selector->addItem(QStringLiteral("Français"), QStringLiteral("fr_FR"));
    selector->addItem(QStringLiteral("简体中文"), QStringLiteral("zh_CN"));
    selector->setCurrentIndex(selector->findData(selected()));
    QObject::connect(selector, QOverload<int>::of(&QComboBox::currentIndexChanged),
                     selector, [selector, parent, showConfirmation](int index) {
        if (index < 0) return;
        QSettings prefs(QStringLiteral("BtrfsAssistantHarbor"), QStringLiteral("Harbor"));
        prefs.setValue(QStringLiteral("ui/language"), selector->itemData(index));
        prefs.sync();
        if (showConfirmation) {
            if (prefs.status() == QSettings::NoError) {
                QMessageBox::information(parent,
                    QCoreApplication::translate("HarborLanguage", "Language saved"),
                    QCoreApplication::translate("HarborLanguage",
                        "Close and reopen Harbor to apply the selected language to every screen."));
            } else {
                QMessageBox::warning(parent,
                    QCoreApplication::translate("HarborLanguage", "Language setting failed"),
                    QCoreApplication::translate("HarborLanguage",
                        "The language preference could not be saved."));
            }
        }
    });
    return selector;
}
} // namespace HarborLanguage
