import type { CloudinaryImageResponse } from "../../types/cloudinary/CloudinaryImageResponse";

export interface ICloudinariImageAPIService {
    addOrChangeImage(image: File): Promise<CloudinaryImageResponse>;
}
