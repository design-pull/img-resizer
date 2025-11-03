; build_installer.iss
; Inno Setup スクリプト（new_icon.ico を使用）

[Setup]
AppName=ImgResizer
AppVersion=0.1.0
DefaultDirName={autopf}\ImgResizer
DefaultGroupName=ImgResizer
OutputBaseFilename=ImgResizer_Installer
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "japanese"; MessagesFile: "compiler:Languages\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにショートカットを作成する"; GroupDescription: "追加タスク"; Flags: unchecked

[Files]
Source: "dist\ImgResizer.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
;
Name: "{group}\ImgResizer"; Filename: "{app}\ImgResizer.exe"; WorkingDir: "{app}"; IconFilename: "assets\new_icon.ico"
Name: "{commondesktop}\ImgResizer"; Filename: "{app}\ImgResizer.exe"; Tasks: desktopicon; WorkingDir: "{app}"; IconFilename: "assets\new_icon.ico"

[Run]
Filename: "{app}\ImgResizer.exe"; Description: "{cm:LaunchProgram,ImgResizer}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
;

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
