class Macmailapp < Formula
  desc "CLI for Apple Mail.app"
  homepage "https://github.com/bizshuk/macmailapp"
  url "https://github.com/bizshuk/macmailapp/releases/download/v0.1.0/mail.zip"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
  version "0.1.0"

  def install
    bin.install "mail"
  end

  test do
    assert_match "mail", shell_output("#{bin}/mail --help")
  end
end