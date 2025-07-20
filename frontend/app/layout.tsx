import "./globals.css";
import Header from "./components/header";
import Nav from "./components/nav";
import { ChatProvider } from "./context/ChatContext"; // <-- Import Provider
import ChatWidget from "./components/ChatWidget"; // <-- Import Widget

export const metadata = {
  title: "CogniSuite",
  description: "An integrated suite of AI-powered tools.",
};

export default function RootLayout({ children }: any) {
  return (
    <html lang="en">
      <ChatProvider>
        <body className="bg-gray-900 text-gray-100 flex h-screen">
          <Nav />
          <main className="flex-1 flex flex-col">
            <Header />
            <div className="flex-1 p-8 overflow-y-auto">
              {children}
            </div>
          </main>
          <ChatWidget /> {/* <-- Render Widget */}
        </body>
      </ChatProvider>
    </html>
  );
}