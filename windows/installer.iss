#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif

[Setup]
AppId={{F703E260-445B-4B85-A1ED-D289BDA64E64}
AppName=Weekly Report
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\WeeklyReport
DefaultGroupName=Weekly Report
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=dist\installer
OutputBaseFilename=WeeklyReport-{#AppVersion}-Setup
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\WeeklyReport.exe
CloseApplications=yes
DisableProgramGroupPage=yes
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"

[Files]
Source: "dist\WeeklyReport\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Weekly Report"; Filename: "{app}\WeeklyReport.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\Weekly Report"; Filename: "{app}\WeeklyReport.exe"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\WeeklyReport.exe"; Description: "Launch Weekly Report"; Flags: nowait postinstall skipifsilent
