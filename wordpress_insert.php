<?php
// Include the necessary WordPress files
require_once('wp-load.php');
require_once('wp-admin/includes/file.php');
require_once('wp-admin/includes/image.php');
require_once('wp-admin/includes/media.php');
require_once('wp-admin/includes/post.php');

kses_remove_filters();


// Load the PHPExcel library to read the Excel file
require 'vendor/autoload.php';
use PhpOffice\PhpSpreadsheet\IOFactory;
use PhpOffice\PhpSpreadsheet\Shared\Date;

// Load the Excel file
$file = 'p.xlsx'; // Update with the actual path
$spreadsheet = IOFactory::load($file);

// Get the first sheet
$sheet = $spreadsheet->getActiveSheet();
$highestRow = $sheet->getHighestRow(); 
$highestColumn = $sheet->getHighestColumn(); 

// Loop through each row of the sheet
for ($row = 1; $row <= $highestRow; $row++) { 
	echo "starting";
	echo $row;
$title = $sheet->getCell('A'.$row)->getValue(); // Assuming 'A' column has post titles
    $content = $sheet->getCell('B'.$row)->getValue(); // Assuming 'B' column has post content
    $image_full_path = $sheet->getCell('D'.$row)->getValue(); // Assuming 'C' column has the full image path
    $post_date = $sheet->getCell('C'.$row)->getValue(); // Assuming 'D' column has post date

    // Convert Excel date to MySQL date format if necessary
    //if (Date::isDateTime($sheet->getCell('D'.$row))) {
     //   $post_date = date('Y-m-d H:i:s', Date::excelToTimestamp($post_date));
   // } else {
  //      echo "error";
//		exit(1);
//    }

    // Prepare the post array


	

    $post_data = array(
        'post_title'    => wp_strip_all_tags($title),
        'post_content'  => $content,
        'post_status'   => 'publish', // or 'draft' if you want to save them as drafts
		'post_category' => 5, 
        'post_author'   => 1, // Set to the desired author ID
		'post_date'     => $post_date, // Set the post date

    );

    // Insert the post into the database
    $post_id = wp_insert_post($post_data);


    if ($image_full_path && !empty($image_full_path) && $post_id) {
        // Combine the WP installation path with the image path from Excel
        $image_path = '/var/www/html' . $image_full_path;

        if (file_exists($image_path)) {
            $filetype = wp_check_filetype(basename($image_path), null);
            $attachment = array(
                'guid'           => get_site_url() . $image_full_path,
                'post_mime_type' => $filetype['type'],
                'post_title'     => sanitize_file_name(basename($image_path)),
                'post_content'   => '',
                'post_status'    => 'inherit'
            );

            $attachment_id = wp_insert_attachment($attachment, $image_path, $post_id);

            // Generate the metadata for the attachment and update the database record.
            $attach_data = wp_generate_attachment_metadata($attachment_id, $image_path);
            wp_update_attachment_metadata($attachment_id, $attach_data);

            // Set the featured image
            set_post_thumbnail($post_id, $attachment_id);
        }
    }
}

?>

 
