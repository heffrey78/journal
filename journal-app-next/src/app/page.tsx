import Link from 'next/link';
import Image from 'next/image';
import MainLayout from '@/components/layout/MainLayout';
import Button from '@/components/ui/Button';

export default function Home() {
  return (
    <MainLayout>
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900 dark:text-white">
            Welcome to Your Journal
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
            Capture your thoughts, memories, and ideas in a secure and organized way.
            Start writing today.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl w-full mb-12">
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">Write Anywhere</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Access your journal from any device with our responsive design.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">Powerful Search</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Quickly find entries with our advanced search functionality.
            </p>
          </div>
          <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-white">Rich Formatting</h2>
            <p className="text-gray-600 dark:text-gray-300">
              Express yourself with Markdown formatting and media attachments.
            </p>
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/entries/new">
            <Button size="lg">
              Create New Entry
            </Button>
          </Link>
          <Link href="/entries">
            <Button variant="secondary" size="lg">
              View All Entries
            </Button>
          </Link>
        </div>
      </div>
    </MainLayout>
  );
}
