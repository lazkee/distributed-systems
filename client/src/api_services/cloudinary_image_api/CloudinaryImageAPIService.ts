import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { ICloudinariImageAPIService } from "./ICloudinaryImageAPIService";
import type { CloudinaryImageResponse } from "../../types/cloudinary/CloudinaryImageResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/users";

export const cloudinaryApi: ICloudinariImageAPIService = {
  async addOrChangeImage(image: File, token: string): Promise<CloudinaryImageResponse> {
    try {
      const formData = new FormData();
      formData.append("image", image);

    const res = await axios.post<CloudinaryImageResponse>(
    `${API_URL}/set-profile-picture`,
    formData,
    {
        headers: {
        Authorization: `Bearer ${token}`
        },
    }
    );

      return res.data;
    } catch (error) {
      let message = "Image upload error";

      if (isAxiosError(error)) {
        message = error.response?.data?.message || message;
      }

      return {
        success: false,
        message,
        data: { url: "" },
      } as CloudinaryImageResponse;
    }
  },
};
