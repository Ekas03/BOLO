<?php
require_once('tcpdf/tcpdf.php');

// Проверяем, задан ли параметр folder в URL-адресе
if (isset($_GET['folder'])) {
    $folderName = $_GET['folder'];
    $jsonFile = $folderName . '/images.json';
    $jsonData = file_get_contents($jsonFile);

    // Если строка JSON начинается с .[, удаляем только точку из начала
    if (substr($jsonData, 0, 1) === '.') {
        $jsonData = substr($jsonData, 1);
    }

    // Декодируем JSON-строку в массив
    $data = json_decode($jsonData, true);
    // Проверяем существование указанной папки
    if (is_dir($folderName)) {
        // Формируем путь к файлу PDF внутри папки c1
        $pdfFileName = $folderName . '/images.pdf';
        echo $folderName;
        echo ' ';
        // Создаем новый PDF документ
        class BOLO_PDF extends TCPDF {
            public function Header() {
                // Set left margin
                $this->SetLeftMargin(10);
                // Set top margin
                $this->SetTopMargin(50);
                // Add logo
                $image_file = 'bolo_logo.jpg';
                $this->Image($image_file, 10, 10, 25);
                // Set font
                $this->SetFont('freeserif', 'B', 15);
                // Title
                $title = "BOLO Bot";
                $this->SetY(35);
                $this->Cell(0, 0, $title, 0, false, 'C', 0, '', 0, false, 'M', 'M');
                $this->Ln(10);
            }
            public function Footer() {
                // Position at 15 mm from bottom
                $this->SetY(-15);
                // Set font
                $this->SetFont('freeserif', 'I', 8);
                // Add a bottom line
                $this->SetLineWidth(0.3);
                $this->Line(10, $this->getPageHeight() - 15, $this->getPageWidth() - 10, $this->getPageHeight() - 15);
                // Page number
                $this->Cell(0, 10, 'Страница ' . $this->getAliasNumPage() . '/' . $this->getAliasNbPages(), 0, false, 'C', 0, '', 0, false, 'T', 'M');
    }
        }

        $pdf = new BOLO_PDF('P', 'mm', 'A4', true, 'UTF-8', false);
        $pdf->SetFont('freeserif', '', 15);
        // Устанавливаем отступы
        $pdf->SetMargins(15, 15, 15);
        
        // Получаем список файлов в указанной папке
        $imageFiles = glob($folderName . '/*.{jpg,jpeg,png,gif}', GLOB_BRACE);

        if ($data !== null) {
            // Перебираем каждый элемент JSON
            foreach ($data as $item) {
                // Получаем путь к изображению и заголовок
                $photoPath = $item['PhotoPath'];
                $title = $item['Title'];
        
                // Добавляем новую страницу
                $pdf->AddPage();
        
                // Получаем размеры изображения
                list($width, $height) = getimagesize($folderName . '/' . $photoPath);
        
                // Масштабируем изображение, чтобы оно поместилось на страницу PDF
                $scale = min(180 / $width, 257 / $height); // 180x257 мм - размер A5 страницы
                $newWidth = $width * $scale;
                $newHeight = $height * $scale;
        
                // Вставляем изображение на страницу
                $pdf->Image($folderName . '/' . $photoPath, null, null, $newWidth, $newHeight);
        
                // Установка координат для текста (в данном случае, координаты левого верхнего угла)
                $pdf->SetXY(20, 40);
                
                // Установка шрифта и размера текста
                $pdf->SetFont('freeserif', '', 15);
        
                // Добавление текста
                $pdf->Cell(0, 10, $title, 0, 1);
            }

            // Записываем PDF в файл
            $pdf->Output(__DIR__ . '/' . $pdfFileName, 'F');

            echo 'PDF сгенерирован: <a href="' . $pdfFileName . '">' . $pdfFileName . '</a>';
        } else {
            echo 'В указанной папке нет изображений.';
        }
    } else {
        echo 'Указанная папка не существует.';
    }
} else {
    echo 'Не указан параметр folder в URL-адресе.';
}
?>
